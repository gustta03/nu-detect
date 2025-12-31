"""
Módulo de Agregação Temporal - Para Processamento de Vídeo

Um único frame NSFW não é suficiente para confirmar nudez.
Considera nudez confirmada apenas se:
- Aparecer em N frames consecutivos, OU
- Ultrapassar um score acumulado ao longo do tempo
"""

from typing import List, Dict, Optional
from collections import deque
import logging

try:
    from .severity_classifier import SeverityLevel
except ImportError:
    try:
        from severity_classifier import SeverityLevel
    except ImportError:
        from enum import Enum
        class SeverityLevel(Enum):
            SAFE = "SAFE"
            SUGGESTIVE = "SUGGESTIVE"
            NSFW = "NSFW"


class TemporalAggregator:
    """
    Agregador temporal para processamento de vídeo.

    Filtra falsos positivos temporais e confirma nudez apenas
    quando há consistência entre múltiplos frames.
    """

    def __init__(self,
                 min_consecutive_frames: int = 3,
                 min_accumulated_score: float = 2.0,
                 window_size: int = 10,
                 debug: bool = False):
        """
        Args:
            min_consecutive_frames: Número mínimo de frames consecutivos NSFW
            min_accumulated_score: Score acumulado mínimo ao longo do tempo
            window_size: Tamanho da janela deslizante para análise
            debug: Se True, habilita logs detalhados
        """
        self.min_consecutive_frames = min_consecutive_frames
        self.min_accumulated_score = min_accumulated_score
        self.window_size = window_size
        self.debug = debug
        self.logger = logging.getLogger(__name__)


        self.frame_window = deque(maxlen=window_size)


        self.consecutive_nsfw_count = 0


        self.accumulated_score = 0.0


        self.total_frames_processed = 0
        self.total_nsfw_frames = 0
        self.total_suggestive_frames = 0
        self.total_safe_frames = 0

    def add_frame(self, severity_result: Dict) -> Dict:
        """
        Adiciona um frame à análise temporal.

        Args:
            severity_result: Resultado de SeverityClassifier.classify()

        Returns:
            Dicionário com resultado agregado:
            {
                'confirmed_nudity': bool,
                'severity': SeverityLevel,
                'confidence': float,
                'consecutive_frames': int,
                'accumulated_score': float,
                'reason': str
            }
        """
        severity = SeverityLevel(severity_result['level'])
        confidence = severity_result.get('confidence', 0.0)


        frame_data = {
            'severity': severity,
            'confidence': confidence,
            'timestamp': len(self.frame_window)
        }
        self.frame_window.append(frame_data)


        self.total_frames_processed += 1
        if severity == SeverityLevel.NSFW:
            self.total_nsfw_frames += 1
        elif severity == SeverityLevel.SUGGESTIVE:
            self.total_suggestive_frames += 1
        else:
            self.total_safe_frames += 1


        if severity == SeverityLevel.NSFW:
            self.consecutive_nsfw_count += 1
            self.accumulated_score += confidence
        else:

            if severity == SeverityLevel.SAFE:
                self.consecutive_nsfw_count = 0

                self.accumulated_score = max(0.0, self.accumulated_score - 0.1)
            else:

                self.accumulated_score = max(0.0, self.accumulated_score - 0.05)


        confirmed_nudity = False
        reason = ""


        if self.consecutive_nsfw_count >= self.min_consecutive_frames:
            confirmed_nudity = True
            reason = f"Nudez confirmada: {self.consecutive_nsfw_count} frames NSFW consecutivos"


        elif self.accumulated_score >= self.min_accumulated_score:
            confirmed_nudity = True
            reason = f"Nudez confirmada: score acumulado {self.accumulated_score:.2f} >= {self.min_accumulated_score}"


        if not confirmed_nudity and len(self.frame_window) >= self.window_size:
            nsfw_in_window = sum(1 for f in self.frame_window
                               if f['severity'] == SeverityLevel.NSFW)
            nsfw_ratio = nsfw_in_window / len(self.frame_window)

            if nsfw_ratio >= 0.6:
                confirmed_nudity = True
                reason = f"Nudez confirmada: {nsfw_ratio:.1%} dos frames na janela são NSFW"


        if confirmed_nudity:
            final_severity = SeverityLevel.NSFW
        elif severity == SeverityLevel.SUGGESTIVE:
            final_severity = SeverityLevel.SUGGESTIVE
        else:
            final_severity = SeverityLevel.SAFE

        if self.debug:
            self.logger.debug(
                f"Frame {len(self.frame_window)}: "
                f"severity={severity.value}, "
                f"consecutive={self.consecutive_nsfw_count}, "
                f"accumulated={self.accumulated_score:.2f}, "
                f"confirmed={confirmed_nudity}"
            )

        return {
            'confirmed_nudity': confirmed_nudity,
            'severity': final_severity,
            'level': final_severity.value,
            'confidence': confidence,
            'consecutive_frames': self.consecutive_nsfw_count,
            'accumulated_score': self.accumulated_score,
            'reason': reason if confirmed_nudity else 'Nudez não confirmada temporalmente',
            'frame_severity': severity_result
        }

    def reset(self):
        """Reseta o agregador (útil para processar múltiplos vídeos)."""
        self.frame_window.clear()
        self.consecutive_nsfw_count = 0
        self.accumulated_score = 0.0
        self.total_frames_processed = 0
        self.total_nsfw_frames = 0
        self.total_suggestive_frames = 0
        self.total_safe_frames = 0

    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas cumulativas de TODOS os frames processados.

        Nota: A janela deslizante é usada apenas para a lógica de agregação temporal,
        mas as estatísticas finais mostram todos os frames processados.
        """
        if self.total_frames_processed == 0:
            return {
                'total_frames': 0,
                'nsfw_frames': 0,
                'suggestive_frames': 0,
                'safe_frames': 0,
                'nsfw_ratio': 0.0,
                'consecutive_nsfw': 0,
                'accumulated_score': 0.0
            }

        return {
            'total_frames': self.total_frames_processed,
            'nsfw_frames': self.total_nsfw_frames,
            'suggestive_frames': self.total_suggestive_frames,
            'safe_frames': self.total_safe_frames,
            'nsfw_ratio': self.total_nsfw_frames / self.total_frames_processed if self.total_frames_processed > 0 else 0.0,
            'consecutive_nsfw': self.consecutive_nsfw_count,
            'accumulated_score': self.accumulated_score
        }

