"""
Módulo de Classificação Hierárquica de Severidade

Classifica cada frame/imagem em:
- SAFE: Sem conteúdo sensível
- SUGGESTIVE: Conteúdo sugestivo (ex: seios sem mamilos)
- NSFW: Conteúdo explícito (genitália, ânus)
"""

from typing import Dict, List
from enum import Enum
import logging

# Importação condicional para evitar circular
try:
    from nudity_analyzer import AnatomicalPart
except ImportError:
    # Fallback se não conseguir importar (para evitar circular)
    class AnatomicalPart:
        GENITALIA = 'genitalia'
        ANUS = 'anus'
        BREAST = 'breast'
        NIPPLE = 'nipple'
        BUTTOCKS = 'buttocks'
        OTHER = 'other'


class SeverityLevel(Enum):
    """Níveis de severidade."""
    SAFE = "SAFE"
    SUGGESTIVE = "SUGGESTIVE"
    NSFW = "NSFW"


class SeverityClassifier:
    """
    Classificador hierárquico de severidade.
    
    Regras:
    - Genitália ou ânus → sempre NSFW
    - Seios sem mamilos → pode ser SUGGESTIVE
    - Múltiplas partes correlatas → aumenta severidade
    """
    
    def __init__(self, debug: bool = False):
        """
        Args:
            debug: Se True, habilita logs detalhados
        """
        self.debug = debug
        self.logger = logging.getLogger(__name__)
    
    def classify(self, nudity_result: Dict) -> Dict:
        """
        Classifica severidade baseado no resultado da análise de nudez.
        
        Args:
            nudity_result: Resultado de NudityAnalyzer.evaluate_nudity()
            
        Returns:
            Dicionário com classificação:
            {
                'severity': SeverityLevel,
                'level': str,  # 'SAFE', 'SUGGESTIVE', ou 'NSFW'
                'confidence': float,
                'reason': str,  # Justificativa da classificação
                'anatomical_types': List[str],
                'parts': List[AnatomicalPart]
            }
        """
        if not nudity_result.get('is_nudity', False):
            return {
                'severity': SeverityLevel.SAFE,
                'level': SeverityLevel.SAFE.value,
                'confidence': 0.0,
                'reason': 'Nenhuma nudez detectada',
                'anatomical_types': [],
                'parts': []
            }
        
        parts = nudity_result.get('parts', [])
        anatomical_types = set(nudity_result.get('anatomical_types', []))
        confidence = nudity_result.get('confidence', 0.0)
        
        # Regra 1: Genitália ou ânus → sempre NSFW
        if AnatomicalPart.GENITALIA in anatomical_types or \
           AnatomicalPart.ANUS in anatomical_types:
            return {
                'severity': SeverityLevel.NSFW,
                'level': SeverityLevel.NSFW.value,
                'confidence': confidence,
                'reason': 'Genitália ou ânus detectado - conteúdo explícito',
                'anatomical_types': list(anatomical_types),
                'parts': parts
            }
        
        # Regra 2: Seios sem mamilos → SUGGESTIVE (se score não muito alto)
        if AnatomicalPart.BREAST in anatomical_types and \
           AnatomicalPart.NIPPLE not in anatomical_types:
            # Se score muito alto, pode ser NSFW mesmo sem mamilo explícito
            if confidence >= 0.85:
                return {
                    'severity': SeverityLevel.NSFW,
                    'level': SeverityLevel.NSFW.value,
                    'confidence': confidence,
                    'reason': 'Seios detectados com alta confiança - possível conteúdo explícito',
                    'anatomical_types': list(anatomical_types),
                    'parts': parts
                }
            else:
                return {
                    'severity': SeverityLevel.SUGGESTIVE,
                    'level': SeverityLevel.SUGGESTIVE.value,
                    'confidence': confidence,
                    'reason': 'Seios detectados sem mamilos - conteúdo sugestivo',
                    'anatomical_types': list(anatomical_types),
                    'parts': parts
                }
        
        # Regra 3: Mamilos → NSFW
        if AnatomicalPart.NIPPLE in anatomical_types:
            return {
                'severity': SeverityLevel.NSFW,
                'level': SeverityLevel.NSFW.value,
                'confidence': confidence,
                'reason': 'Mamilos detectados - conteúdo explícito',
                'anatomical_types': list(anatomical_types),
                'parts': parts
            }
        
        # Regra 4: Nádegas → depende do contexto
        if AnatomicalPart.BUTTOCKS in anatomical_types:
            # Se combinado com outras partes ou score alto → NSFW
            if len(anatomical_types) > 1 or confidence >= 0.8:
                return {
                    'severity': SeverityLevel.NSFW,
                    'level': SeverityLevel.NSFW.value,
                    'confidence': confidence,
                    'reason': 'Nádegas detectadas com outras partes ou alta confiança',
                    'anatomical_types': list(anatomical_types),
                    'parts': parts
                }
            else:
                return {
                    'severity': SeverityLevel.SUGGESTIVE,
                    'level': SeverityLevel.SUGGESTIVE.value,
                    'confidence': confidence,
                    'reason': 'Nádegas detectadas - conteúdo sugestivo',
                    'anatomical_types': list(anatomical_types),
                    'parts': parts
                }
        
        # Regra 5: Múltiplas partes correlatas → aumenta severidade
        if len(anatomical_types) >= 2:
            return {
                'severity': SeverityLevel.NSFW,
                'level': SeverityLevel.NSFW.value,
                'confidence': confidence,
                'reason': f'Múltiplas partes anatômicas detectadas ({len(anatomical_types)} tipos)',
                'anatomical_types': list(anatomical_types),
                'parts': parts
            }
        
        # Fallback: baseado em confiança
        if confidence >= 0.75:
            return {
                'severity': SeverityLevel.NSFW,
                'level': SeverityLevel.NSFW.value,
                'confidence': confidence,
                'reason': 'Alta confiança na detecção',
                'anatomical_types': list(anatomical_types),
                'parts': parts
            }
        elif confidence >= 0.5:
            return {
                'severity': SeverityLevel.SUGGESTIVE,
                'level': SeverityLevel.SUGGESTIVE.value,
                'confidence': confidence,
                'reason': 'Confiança moderada na detecção',
                'anatomical_types': list(anatomical_types),
                'parts': parts
            }
        else:
            return {
                'severity': SeverityLevel.SAFE,
                'level': SeverityLevel.SAFE.value,
                'confidence': confidence,
                'reason': 'Baixa confiança na detecção',
                'anatomical_types': list(anatomical_types),
                'parts': parts
            }

