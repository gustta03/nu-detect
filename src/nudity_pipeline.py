"""
Pipeline Principal de Detecção de Nudez - Arquitetura Multiestágio

Orquestra todos os estágios:
1. Detecção de humanos (YOLOv8)
2. Análise de nudez (NudeNet apenas em bounding boxes)
3. Classificação de severidade (SAFE, SUGGESTIVE, NSFW)
4. Agregação temporal (para vídeo)
5. Observabilidade (logs estruturados)
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

from .human_detector import HumanDetector
from .nudity_analyzer import NudityAnalyzer
from .severity_classifier import SeverityClassifier, SeverityLevel
from .temporal_aggregator import TemporalAggregator
from .observability import ObservabilityLogger


class NudityDetectionPipeline:
    """
    Pipeline completo de detecção de nudez.

    Implementa arquitetura multiestágio conforme especificação:
    - Estágio 1: Detecção de humanos
    - Estágio 2: Análise de nudez (apenas em bounding boxes)
    - Estágio 3: Classificação hierárquica
    - Estágio 4: Agregação temporal (vídeo)
    - Observabilidade: Logs estruturados
    """

    def __init__(self,

                 yolo_model_size: str = 'n',
                 human_confidence_threshold: float = 0.25,


                 nudity_base_threshold: float = 0.3,
                 spatial_grouping_threshold: float = 0.3,
                 min_correlated_parts: int = 2,


                 min_consecutive_frames: int = 3,
                 min_accumulated_score: float = 2.0,
                 temporal_window_size: int = 10,


                 log_file: Optional[str] = None,
                 debug: bool = False):
        """
        Inicializa o pipeline completo.

        Args:
            yolo_model_size: Tamanho do modelo YOLO ('n', 's', 'm', 'l', 'x')
            human_confidence_threshold: Threshold para detecção de humanos
            nudity_base_threshold: Threshold base para análise de nudez
            spatial_grouping_threshold: Threshold para agrupamento espacial
            min_correlated_parts: Mínimo de partes correlatas para confirmar nudez
            min_consecutive_frames: Mínimo de frames consecutivos NSFW (vídeo)
            min_accumulated_score: Score acumulado mínimo (vídeo)
            temporal_window_size: Tamanho da janela temporal
            log_file: Arquivo para logs estruturados (None = apenas console)
            debug: Se True, habilita modo debug completo
        """
        self.debug = debug


        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)


        self.logger.info("Inicializando pipeline de detecção de nudez...")

        try:
            self.human_detector = HumanDetector(
                model_size=yolo_model_size,
                confidence_threshold=human_confidence_threshold,
                debug=debug
            )
            self.logger.info("✓ Detector de humanos inicializado")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar detector de humanos: {e}")
            raise

        try:
            self.nudity_analyzer = NudityAnalyzer(
                base_threshold=nudity_base_threshold,
                spatial_grouping_threshold=spatial_grouping_threshold,
                min_correlated_parts=min_correlated_parts,
                debug=debug
            )
            self.logger.info("✓ Analisador de nudez inicializado")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar analisador de nudez: {e}")
            raise

        self.severity_classifier = SeverityClassifier(debug=debug)
        self.logger.info("✓ Classificador de severidade inicializado")

        self.temporal_aggregator = TemporalAggregator(
            min_consecutive_frames=min_consecutive_frames,
            min_accumulated_score=min_accumulated_score,
            window_size=temporal_window_size,
            debug=debug
        )
        self.logger.info("✓ Agregador temporal inicializado")

        self.observability = ObservabilityLogger(
            log_file=log_file,
            debug=debug,
            structured_logging=True
        )
        self.logger.info("✓ Sistema de observabilidade inicializado")

        self.logger.info("Pipeline inicializado com sucesso!")

    def process_image(self, image_path: str) -> Dict:
        """
        Processa uma imagem completa através do pipeline.

        Args:
            image_path: Caminho para a imagem

        Returns:
            Dicionário com resultado completo:
            {
                'image_path': str,
                'humans_detected': int,
                'nudity_detected': bool,
                'severity': str,  # 'SAFE', 'SUGGESTIVE', 'NSFW'
                'confidence': float,
                'human_detections': List[Dict],
                'nudity_result': Dict,
                'severity_result': Dict,
                'parts_detected': List[Dict]
            }
        """
        try:

            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Erro ao carregar imagem: {image_path}")

            height, width = image.shape[:2]


            self.logger.debug(f"Estágio 1: Detectando humanos em {image_path}")
            human_detections = self.human_detector.detect(image_path)

            if not human_detections:

                result = {
                    'image_path': image_path,
                    'humans_detected': 0,
                    'nudity_detected': False,
                    'severity': SeverityLevel.SAFE.value,
                    'confidence': 0.0,
                    'human_detections': [],
                    'nudity_result': {'is_nudity': False, 'confidence': 0.0},
                    'severity_result': {
                        'level': SeverityLevel.SAFE.value,
                        'confidence': 0.0,
                        'reason': 'Nenhuma pessoa detectada'
                    },
                    'parts_detected': []
                }

                self.observability.log_image_processing(
                    image_path, [], result['nudity_result'], result['severity_result']
                )

                return result


            self.logger.debug(f"Estágio 2: Analisando nudez em {len(human_detections)} pessoa(s)")
            all_parts = []

            for human_det in human_detections:
                bbox = human_det['bbox']
                x1, y1, x2, y2 = bbox


                roi = self.human_detector.extract_roi(image, bbox)


                parts = self.nudity_analyzer.analyze_roi(
                    roi,
                    image_coords=(x1, y1)
                )
                all_parts.extend(parts)


            nudity_result = self.nudity_analyzer.evaluate_nudity(
                all_parts, width, height
            )


            self.logger.debug("Estágio 3: Classificando severidade")
            severity_result = self.severity_classifier.classify(nudity_result)


            self.observability.log_image_processing(
                image_path, human_detections, nudity_result, severity_result
            )


            result = {
                'image_path': image_path,
                'humans_detected': len(human_detections),
                'nudity_detected': nudity_result.get('is_nudity', False),
                'severity': severity_result.get('level', SeverityLevel.SAFE.value),
                'confidence': severity_result.get('confidence', 0.0),
                'human_detections': human_detections,
                'nudity_result': nudity_result,
                'severity_result': severity_result,
                'parts_detected': [part.to_dict() for part in all_parts]
            }

            return result

        except Exception as e:
            self.observability.log_pipeline_error('process_image', e, {'image_path': image_path})
            raise

    def process_video_frame(self,
                          frame_path: str,
                          frame_index: int,
                          frame_timestamp: float) -> Dict:
        """
        Processa um frame de vídeo através do pipeline.

        Args:
            frame_path: Caminho para o frame
            frame_index: Índice do frame
            frame_timestamp: Timestamp do frame em segundos

        Returns:
            Dicionário com resultado incluindo agregação temporal
        """
        try:

            image_result = self.process_image(frame_path)


            temporal_result = self.temporal_aggregator.add_frame(
                image_result['severity_result']
            )


            self.observability.log_video_frame(
                frame_index,
                frame_timestamp,
                frame_path,
                image_result['human_detections'],
                image_result['nudity_result'],
                image_result['severity_result'],
                temporal_result
            )


            result = image_result.copy()
            result.update({
                'frame_index': frame_index,
                'frame_timestamp': frame_timestamp,
                'temporal_result': temporal_result,
                'confirmed_nudity': temporal_result.get('confirmed_nudity', False),
                'final_severity': temporal_result.get('level', SeverityLevel.SAFE.value),
                'consecutive_frames': temporal_result.get('consecutive_frames', 0),
                'accumulated_score': temporal_result.get('accumulated_score', 0.0)
            })

            return result

        except Exception as e:
            self.observability.log_pipeline_error(
                'process_video_frame',
                e,
                {'frame_path': frame_path, 'frame_index': frame_index}
            )
            raise

    def reset_temporal_aggregator(self):
        """Reseta o agregador temporal (útil para processar múltiplos vídeos)."""
        self.temporal_aggregator.reset()

    def get_temporal_statistics(self) -> Dict:
        """Retorna estatísticas do agregador temporal."""
        return self.temporal_aggregator.get_statistics()

