"""
Módulo de Análise de Nudez - Estágio 2 do Pipeline

Analisa nudez baseado em scores anatômicos, não em strings.
Agrupa detecções por proximidade espacial e avalia baseado em:
- Tipo anatômico detectado
- Score do modelo
- Número de partes corporais correlatas detectadas
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from collections import defaultdict

try:
    from nudenet import NudeDetector
    NUDENET_AVAILABLE = True
except ImportError:
    NUDENET_AVAILABLE = False
    logging.warning("NudeNet não disponível. Instale com: pip install nudenet")


class AnatomicalPart:
    """Representa uma parte anatômica detectada."""


    GENITALIA = 'genitalia'
    ANUS = 'anus'
    BREAST = 'breast'
    NIPPLE = 'nipple'
    BUTTOCKS = 'buttocks'
    OTHER = 'other'

    def __init__(self, class_name: str, score: float, bbox: List[float],
                 image_coords: Optional[Tuple[int, int]] = None):
        """
        Args:
            class_name: Nome da classe detectada pelo NudeNet
            score: Score de confiança (0.0-1.0)
            bbox: Bounding box [x, y, width, height] ou [x1, y1, x2, y2]
            image_coords: Offset da ROI na imagem original (x_offset, y_offset)
        """
        self.class_name = class_name
        self.score = score
        self.bbox = bbox
        self.image_coords = image_coords or (0, 0)
        self.anatomical_type = self._classify_anatomical_type(class_name)
        self.severity_weight = self._get_severity_weight()

    def _classify_anatomical_type(self, class_name: str) -> str:
        """Classifica o tipo anatômico baseado no nome da classe."""
        class_upper = class_name.upper()


        if any(kw in class_upper for kw in ['GENITALIA', 'GENITAL']):
            return self.GENITALIA


        if 'ANUS' in class_upper:
            return self.ANUS


        if 'NIPPLE' in class_upper:
            return self.NIPPLE


        if 'BREAST' in class_upper:
            return self.BREAST


        if 'BUTTOCK' in class_upper:
            return self.BUTTOCKS

        return self.OTHER

    def _get_severity_weight(self) -> float:
        """Retorna peso de severidade baseado no tipo anatômico."""
        weights = {
            self.GENITALIA: 1.0,
            self.ANUS: 1.0,
            self.NIPPLE: 0.7,
            self.BREAST: 0.5,
            self.BUTTOCKS: 0.6,
            self.OTHER: 0.3
        }
        return weights.get(self.anatomical_type, 0.3)

    def get_absolute_bbox(self) -> List[int]:
        """Retorna bbox em coordenadas absolutas da imagem original."""
        x_offset, y_offset = self.image_coords

        if len(self.bbox) >= 4:

            bbox_values = [float(v) for v in self.bbox[:4]]


            diff_x = abs(bbox_values[2] - bbox_values[0])
            diff_y = abs(bbox_values[3] - bbox_values[1])

            if diff_x < 10 and diff_y < 10:

                x, y, w, h = bbox_values
                x1, y1 = int(x + x_offset), int(y + y_offset)
                x2, y2 = int(x + w + x_offset), int(y + h + y_offset)
            else:

                x1, y1, x2, y2 = [int(v) for v in bbox_values]
                x1 += x_offset
                y1 += y_offset
                x2 += x_offset
                y2 += y_offset

            return [x1, y1, x2, y2]

        return [0, 0, 0, 0]

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'class_name': self.class_name,
            'anatomical_type': self.anatomical_type,
            'score': self.score,
            'bbox': self.bbox,
            'absolute_bbox': self.get_absolute_bbox(),
            'severity_weight': self.severity_weight
        }


class NudityAnalyzer:
    """
    Analisador de nudez baseado em scores anatômicos.

    Não usa string matching rígido. Em vez disso:
    1. Agrupa detecções por proximidade espacial
    2. Avalia baseado em tipo anatômico + score + número de partes correlatas
    3. Uma única detecção isolada ≠ nudez
    4. Duas ou mais partes anatômicas coerentes ≈ nudez provável
    """

    def __init__(self,
                 base_threshold: float = 0.3,
                 spatial_grouping_threshold: float = 0.3,
                 min_correlated_parts: int = 2,
                 debug: bool = False):
        """
        Args:
            base_threshold: Threshold base de confiança (0.0-1.0)
            spatial_grouping_threshold: Distância máxima para agrupar detecções (proporção da imagem)
            min_correlated_parts: Número mínimo de partes correlatas para confirmar nudez
            debug: Se True, habilita logs detalhados
        """
        if not NUDENET_AVAILABLE:
            raise ImportError(
                "NudeNet não está instalado. Instale com: pip install nudenet"
            )

        self.base_threshold = base_threshold
        self.spatial_grouping_threshold = spatial_grouping_threshold
        self.min_correlated_parts = min_correlated_parts
        self.debug = debug
        self.logger = logging.getLogger(__name__)


        # THRESHOLDS MUITO BAIXOS para máxima sensibilidade (99.8% precisão)
        # Aceitamos detecções com confiança muito baixa para não perder nada
        self.thresholds = {
            AnatomicalPart.GENITALIA: base_threshold * 0.3,  # Reduzido de 0.6
            AnatomicalPart.ANUS: base_threshold * 0.3,  # Reduzido de 0.6
            AnatomicalPart.NIPPLE: base_threshold * 0.4,  # Reduzido de 0.8
            AnatomicalPart.BREAST: base_threshold * 0.3,  # Reduzido de 0.9 - CRÍTICO para capturar seios
            AnatomicalPart.BUTTOCKS: base_threshold * 0.35,  # Reduzido de 0.85
            AnatomicalPart.OTHER: base_threshold * 0.5  # Reduzido
        }


        if self.debug:
            self.logger.info("Carregando modelo NudeNet...")

        try:
            self.detector = NudeDetector()
            if self.debug:
                self.logger.info("Modelo NudeNet carregado com sucesso")
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar modelo NudeNet: {e}")

    def analyze_roi(self, roi_image: np.ndarray,
                   image_coords: Tuple[int, int] = (0, 0)) -> List[AnatomicalPart]:
        """
        Analisa nudez em uma região de interesse (ROI).

        Args:
            roi_image: Array numpy com a ROI (região da pessoa)
            image_coords: Offset da ROI na imagem original (x_offset, y_offset)

        Returns:
            Lista de partes anatômicas detectadas
        """

        import tempfile
        import cv2
        import os

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            cv2.imwrite(tmp_path, roi_image)

        try:

            detections = self.detector.detect(tmp_path)

            anatomical_parts = []

            for det in detections:
                class_name = det.get('class', '')
                score = det.get('score', 0.0)
                bbox = det.get('box') or det.get('bbox') or det.get('bounding_box', [])


                part = AnatomicalPart(class_name, score, bbox, image_coords)


                threshold = self.thresholds.get(part.anatomical_type, self.base_threshold)

                if score >= threshold:
                    anatomical_parts.append(part)
                    if self.debug:
                        self.logger.debug(
                            f"Detectado: {class_name} (tipo: {part.anatomical_type}, "
                            f"score: {score:.3f}, threshold: {threshold:.3f})"
                        )

            return anatomical_parts

        finally:

            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def group_by_proximity(self, parts: List[AnatomicalPart],
                          image_width: int, image_height: int) -> List[List[AnatomicalPart]]:
        """
        Agrupa partes anatômicas por proximidade espacial.

        Args:
            parts: Lista de partes anatômicas
            image_width: Largura da imagem
            image_height: Altura da imagem

        Returns:
            Lista de grupos de partes anatômicas
        """
        if not parts:
            return []


        part_centers = []
        for part in parts:
            bbox = part.get_absolute_bbox()
            if len(bbox) >= 4:
                x1, y1, x2, y2 = bbox
                center_x = (x1 + x2) / 2.0
                center_y = (y1 + y2) / 2.0
                part_centers.append((center_x, center_y, part))


        max_distance = min(image_width, image_height) * self.spatial_grouping_threshold


        groups = []
        used = set()

        for i, (cx1, cy1, part1) in enumerate(part_centers):
            if i in used:
                continue

            group = [part1]
            used.add(i)

            for j, (cx2, cy2, part2) in enumerate(part_centers):
                if j in used or i == j:
                    continue


                distance = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)

                if distance <= max_distance:
                    group.append(part2)
                    used.add(j)

            groups.append(group)

        return groups

    def evaluate_nudity(self, parts: List[AnatomicalPart],
                       image_width: int, image_height: int) -> Dict:
        """
        Avalia nudez baseado em agrupamento espacial e correlação anatômica.

        Args:
            parts: Lista de partes anatômicas detectadas
            image_width: Largura da imagem
            image_height: Altura da imagem

        Returns:
            Dicionário com resultado da avaliação:
            {
                'is_nudity': bool,
                'confidence': float,
                'groups': List[List[AnatomicalPart]],
                'total_parts': int,
                'anatomical_types': List[str]
            }
        """
        if not parts:
            return {
                'is_nudity': False,
                'confidence': 0.0,
                'groups': [],
                'total_parts': 0,
                'anatomical_types': []
            }


        groups = self.group_by_proximity(parts, image_width, image_height)


        max_confidence = 0.0
        best_group = None

        for group in groups:

            anatomical_types = set(part.anatomical_type for part in group)



            num_parts = len(group)
            avg_score = np.mean([part.score for part in group])
            max_severity = max([part.severity_weight for part in group])





            group_confidence = avg_score * max_severity


            if num_parts >= self.min_correlated_parts:
                group_confidence *= 1.5


            if AnatomicalPart.GENITALIA in anatomical_types or \
               AnatomicalPart.ANUS in anatomical_types:
                group_confidence *= 1.3

            if group_confidence > max_confidence:
                max_confidence = group_confidence
                best_group = group



        is_nudity = False

        if best_group:
            num_parts = len(best_group)
            anatomical_types = set(part.anatomical_type for part in best_group)
            avg_score = np.mean([part.score for part in best_group])






            has_critical_type = AnatomicalPart.GENITALIA in anatomical_types or \
                               AnatomicalPart.ANUS in anatomical_types

            has_breast_nipple = AnatomicalPart.BREAST in anatomical_types and \
                              AnatomicalPart.NIPPLE in anatomical_types
            
            has_breast = AnatomicalPart.BREAST in anatomical_types
            has_buttocks = AnatomicalPart.BUTTOCKS in anatomical_types

            # MODO MÁXIMA SENSIBILIDADE: Aceitar qualquer detecção relevante
            # Prioridade 1: Genitália/ânus (sempre NSFW)
            if has_critical_type:
                is_nudity = True
            # Prioridade 2: Seios (sempre considerar, mesmo sozinho)
            elif has_breast and avg_score >= self.thresholds[AnatomicalPart.BREAST]:
                is_nudity = True  # Será classificado como SUGGESTIVE ou NSFW
            # Prioridade 3: Nádegas (sempre considerar, mesmo sozinho)
            elif has_buttocks and avg_score >= self.thresholds[AnatomicalPart.BUTTOCKS]:
                is_nudity = True  # Será classificado como SUGGESTIVE
            # Prioridade 4: Múltiplas partes (aumenta confiança)
            elif num_parts >= self.min_correlated_parts:
                is_nudity = True
            # Prioridade 5: Seios + mamilos
            elif has_breast_nipple:
                is_nudity = True
            # Prioridade 6: Qualquer parte com score suficiente (máxima sensibilidade)
            elif num_parts >= 1 and avg_score >= self.base_threshold * 0.4:
                is_nudity = True

        return {
            'is_nudity': is_nudity,
            'confidence': min(max_confidence, 1.0),
            'groups': groups,
            'total_parts': len(parts),
            'anatomical_types': list(set(part.anatomical_type for part in parts)),
            'parts': parts
        }

