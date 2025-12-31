"""
Módulo de Detecção de Humanos - Estágio 1 do Pipeline

Responsável por detectar presença humana na imagem usando YOLOv8.
Retorna apenas bounding boxes da classe 'person', ignorando outros objetos.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("YOLOv8 não disponível. Instale com: pip install ultralytics")


class HumanDetector:
    """
    Detector de humanos usando YOLOv8.
    
    Detecta exclusivamente a classe 'person' e retorna bounding boxes
    para uso no estágio 2 (análise de nudez).
    """
    
    def __init__(self, model_size: str = 'n', confidence_threshold: float = 0.25, debug: bool = False):
        """
        Inicializa o detector de humanos.
        
        Args:
            model_size: Tamanho do modelo YOLO ('n'=nano, 's'=small, 'm'=medium, 'l'=large, 'x'=xlarge)
            confidence_threshold: Threshold mínimo de confiança para detecção (0.0-1.0)
            debug: Se True, habilita logs detalhados
        """
        if not YOLO_AVAILABLE:
            raise ImportError(
                "YOLOv8 não está instalado. Instale com: pip install ultralytics"
            )
        
        self.model_size = model_size
        self.confidence_threshold = confidence_threshold
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        
        # Carrega modelo YOLOv8 (baixa automaticamente na primeira execução)
        model_name = f'yolov8{model_size}.pt'
        if self.debug:
            self.logger.info(f"Carregando modelo YOLOv8: {model_name}")
        
        try:
            self.model = YOLO(model_name)
            if self.debug:
                self.logger.info("Modelo YOLOv8 carregado com sucesso")
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar modelo YOLOv8: {e}")
    
    def detect(self, image_path: str) -> List[dict]:
        """
        Detecta humanos na imagem.
        
        Args:
            image_path: Caminho para a imagem ou array numpy
            
        Returns:
            Lista de dicionários com detecções de humanos:
            [
                {
                    'bbox': [x1, y1, x2, y2],  # Coordenadas absolutas
                    'confidence': float,        # Score de confiança
                    'class_id': int,           # ID da classe (sempre 0 para 'person')
                    'class_name': 'person'     # Nome da classe
                },
                ...
            ]
        """
        # Carrega imagem
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Erro ao carregar imagem: {image_path}")
        else:
            image = image_path
        
        if image is None:
            raise ValueError("Imagem inválida")
        
        height, width = image.shape[:2]
        
        # Executa detecção
        results = self.model.predict(
            image,
            conf=self.confidence_threshold,
            classes=[0],  # Apenas classe 'person' (ID 0 no COCO)
            verbose=False
        )
        
        detections = []
        
        # Processa resultados
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                if self.debug:
                    self.logger.debug("Nenhuma pessoa detectada")
                continue
            
            for box in boxes:
                # Verifica se é classe 'person' (ID 0)
                class_id = int(box.cls[0])
                if class_id != 0:  # 0 = person no COCO dataset
                    continue
                
                confidence = float(box.conf[0])
                
                # Obtém coordenadas (YOLO retorna no formato xyxy)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Garante que coordenadas estão dentro da imagem
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))
                
                # Valida bbox
                if x2 > x1 and y2 > y1:
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': confidence,
                        'class_id': class_id,
                        'class_name': 'person',
                        'area': (x2 - x1) * (y2 - y1)
                    })
        
        if self.debug:
            self.logger.info(f"Detectadas {len(detections)} pessoa(s) na imagem")
            for i, det in enumerate(detections):
                self.logger.debug(
                    f"  Pessoa {i+1}: bbox={det['bbox']}, "
                    f"confiança={det['confidence']:.3f}, "
                    f"área={det['area']}px²"
                )
        
        return detections
    
    def extract_roi(self, image_path: str, bbox: List[int]) -> np.ndarray:
        """
        Extrai região de interesse (ROI) da imagem baseado no bounding box.
        
        Args:
            image_path: Caminho para a imagem ou array numpy
            bbox: [x1, y1, x2, y2] coordenadas do bounding box
            
        Returns:
            Array numpy com a ROI extraída
        """
        # Carrega imagem
        if isinstance(image_path, str):
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Erro ao carregar imagem: {image_path}")
        else:
            image = image_path
        
        x1, y1, x2, y2 = bbox
        height, width = image.shape[:2]
        
        # Garante coordenadas válidas
        x1 = max(0, min(x1, width))
        y1 = max(0, min(y1, height))
        x2 = max(0, min(x2, width))
        y2 = max(0, min(y2, height))
        
        # Extrai ROI
        roi = image[y1:y2, x1:x2].copy()
        
        return roi

