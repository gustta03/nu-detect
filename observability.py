"""
Módulo de Observabilidade

Fornece logs estruturados por imagem/frame contendo:
- Pessoas detectadas
- Partes anatômicas detectadas
- Scores
- Decisão final
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from severity_classifier import SeverityLevel


class ObservabilityLogger:
    """
    Sistema de observabilidade com logs estruturados.
    
    Permite inspeção completa do pipeline em modo debug.
    """
    
    def __init__(self, 
                 log_file: Optional[str] = None,
                 debug: bool = False,
                 structured_logging: bool = True):
        """
        Args:
            log_file: Caminho para arquivo de log (None = apenas console)
            debug: Se True, habilita logs detalhados
            structured_logging: Se True, usa formato JSON estruturado
        """
        self.log_file = log_file
        self.debug = debug
        self.structured_logging = structured_logging
        
        # Configura logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Handler para arquivo (se especificado)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
        
        self.logger.addHandler(console_handler)
        
        # Formato
        if structured_logging:
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def log_image_processing(self, 
                           image_path: str,
                           human_detections: List[Dict],
                           nudity_result: Dict,
                           severity_result: Dict,
                           timestamp: Optional[float] = None) -> Dict:
        """
        Registra processamento completo de uma imagem.
        
        Args:
            image_path: Caminho da imagem
            human_detections: Lista de detecções de humanos
            nudity_result: Resultado da análise de nudez
            severity_result: Resultado da classificação de severidade
            timestamp: Timestamp do frame (para vídeo)
            
        Returns:
            Dicionário com log estruturado
        """
        log_entry = {
            'timestamp': timestamp or datetime.now().isoformat(),
            'image_path': str(image_path),
            'image_name': Path(image_path).name,
            'stage_1_human_detection': {
                'total_humans': len(human_detections),
                'detections': [
                    {
                        'bbox': det.get('bbox', []),
                        'confidence': det.get('confidence', 0.0),
                        'area': det.get('area', 0)
                    }
                    for det in human_detections
                ]
            },
            'stage_2_nudity_analysis': {
                'is_nudity': nudity_result.get('is_nudity', False),
                'confidence': nudity_result.get('confidence', 0.0),
                'total_parts': nudity_result.get('total_parts', 0),
                'anatomical_types': nudity_result.get('anatomical_types', []),
                'groups': [
                    {
                        'num_parts': len(group),
                        'parts': [
                            {
                                'class_name': part.class_name,
                                'anatomical_type': part.anatomical_type,
                                'score': part.score,
                                'bbox': part.get_absolute_bbox()
                            }
                            for part in group
                        ]
                    }
                    for group in nudity_result.get('groups', [])
                ],
                'parts': [
                    {
                        'class_name': part.class_name,
                        'anatomical_type': part.anatomical_type,
                        'score': part.score,
                        'bbox': part.get_absolute_bbox(),
                        'severity_weight': part.severity_weight
                    }
                    for part in nudity_result.get('parts', [])
                ]
            },
            'stage_3_severity_classification': {
                'severity': severity_result.get('level', 'SAFE'),
                'confidence': severity_result.get('confidence', 0.0),
                'reason': severity_result.get('reason', ''),
                'anatomical_types': severity_result.get('anatomical_types', [])
            },
            'final_decision': {
                'is_nsfw': severity_result.get('level') == SeverityLevel.NSFW.value,
                'is_suggestive': severity_result.get('level') == SeverityLevel.SUGGESTIVE.value,
                'is_safe': severity_result.get('level') == SeverityLevel.SAFE.value,
                'severity': severity_result.get('level', 'SAFE'),
                'confidence': severity_result.get('confidence', 0.0)
            }
        }
        
        # Log estruturado
        if self.structured_logging:
            log_json = json.dumps(log_entry, indent=2, default=str)
            self.logger.info(f"IMAGE_PROCESSING\n{log_json}")
        else:
            self.logger.info(f"Processando imagem: {image_path}")
            self.logger.info(f"  Humanos detectados: {len(human_detections)}")
            self.logger.info(f"  Nudez detectada: {nudity_result.get('is_nudity', False)}")
            self.logger.info(f"  Severidade: {severity_result.get('level', 'SAFE')}")
        
        return log_entry
    
    def log_video_frame(self,
                       frame_index: int,
                       frame_timestamp: float,
                       frame_path: str,
                       human_detections: List[Dict],
                       nudity_result: Dict,
                       severity_result: Dict,
                       temporal_result: Optional[Dict] = None) -> Dict:
        """
        Registra processamento de um frame de vídeo.
        
        Args:
            frame_index: Índice do frame
            frame_timestamp: Timestamp do frame em segundos
            frame_path: Caminho do frame
            human_detections: Lista de detecções de humanos
            nudity_result: Resultado da análise de nudez
            severity_result: Resultado da classificação de severidade
            temporal_result: Resultado da agregação temporal (opcional)
            
        Returns:
            Dicionário com log estruturado
        """
        log_entry = {
            'frame_index': frame_index,
            'frame_timestamp': frame_timestamp,
            'frame_path': str(frame_path),
            'stage_1_human_detection': {
                'total_humans': len(human_detections),
                'detections': [
                    {
                        'bbox': det.get('bbox', []),
                        'confidence': det.get('confidence', 0.0)
                    }
                    for det in human_detections
                ]
            },
            'stage_2_nudity_analysis': {
                'is_nudity': nudity_result.get('is_nudity', False),
                'confidence': nudity_result.get('confidence', 0.0),
                'total_parts': nudity_result.get('total_parts', 0),
                'anatomical_types': nudity_result.get('anatomical_types', [])
            },
            'stage_3_severity_classification': {
                'severity': severity_result.get('level', 'SAFE'),
                'confidence': severity_result.get('confidence', 0.0),
                'reason': severity_result.get('reason', '')
            }
        }
        
        if temporal_result:
            log_entry['stage_4_temporal_aggregation'] = {
                'confirmed_nudity': temporal_result.get('confirmed_nudity', False),
                'severity': temporal_result.get('level', 'SAFE'),
                'consecutive_frames': temporal_result.get('consecutive_frames', 0),
                'accumulated_score': temporal_result.get('accumulated_score', 0.0),
                'reason': temporal_result.get('reason', '')
            }
            log_entry['final_decision'] = {
                'is_nsfw': temporal_result.get('level') == SeverityLevel.NSFW.value,
                'severity': temporal_result.get('level', 'SAFE'),
                'confidence': temporal_result.get('confidence', 0.0),
                'confirmed': temporal_result.get('confirmed_nudity', False)
            }
        else:
            log_entry['final_decision'] = {
                'is_nsfw': severity_result.get('level') == SeverityLevel.NSFW.value,
                'severity': severity_result.get('level', 'SAFE'),
                'confidence': severity_result.get('confidence', 0.0)
            }
        
        # Log estruturado
        if self.structured_logging:
            log_json = json.dumps(log_entry, indent=2, default=str)
            self.logger.debug(f"VIDEO_FRAME\n{log_json}")
        else:
            self.logger.debug(
                f"Frame {frame_index} ({frame_timestamp:.2f}s): "
                f"severity={severity_result.get('level', 'SAFE')}, "
                f"confirmed={temporal_result.get('confirmed_nudity', False) if temporal_result else False}"
            )
        
        return log_entry
    
    def log_pipeline_error(self, stage: str, error: Exception, context: Dict = None):
        """Registra erro em um estágio do pipeline."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        if self.structured_logging:
            log_json = json.dumps(error_entry, indent=2, default=str)
            self.logger.error(f"PIPELINE_ERROR\n{log_json}")
        else:
            self.logger.error(f"Erro no estágio {stage}: {error}")

