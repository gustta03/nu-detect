# Arquitetura do Sistema de Detecção de Nudez

## Visão Geral

Sistema robusto de detecção de nudez em imagens e vídeos implementando arquitetura **pipeline multiestágio** para minimizar falsos positivos em objetos e falsos negativos em humanos parcialmente nus.

## Diagrama do Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT (Imagem/Vídeo)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  ESTÁGIO 1: Detecção de Humanos       │
        │  - YOLOv8 (classe 'person')           │
        │  - Retorna bounding boxes             │
        │  - Ignora imagens sem humanos         │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  ESTÁGIO 2: Análise de Nudez          │
        │  - NudeNet apenas em bounding boxes   │
        │  - Agrupamento espacial               │
        │  - Avaliação por scores anatômicos    │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  ESTÁGIO 3: Classificação Hierárquica │
        │  - SAFE / SUGGESTIVE / NSFW           │
        │  - Thresholds por tipo anatômico      │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  ESTÁGIO 4: Agregação Temporal        │
        │  (Apenas para vídeo)                  │
        │  - Frames consecutivos                 │
        │  - Score acumulado                    │
        └───────────────────┬───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  OBSERVABILIDADE                      │
        │  - Logs estruturados (JSON)           │
        │  - Debug completo                     │
        └───────────────────┬───────────────────┘
                            │
                            ▼
                    OUTPUT (Resultado)
```

## Componentes do Sistema

### 1. Human Detector (`human_detector.py`)

**Responsabilidade**: Detectar presença humana na imagem.

**Tecnologia**: YOLOv8 (Ultralytics)

**Justificativa Técnica**:
- YOLOv8 é um modelo moderno, rápido e preciso para detecção de objetos
- Detecta exclusivamente classe 'person' (ID 0 no COCO dataset)
- Ignora completamente imagens sem presença humana
- Reduz processamento desnecessário no estágio 2

**Parâmetros**:
- `model_size`: Tamanho do modelo ('n'=nano até 'x'=xlarge)
- `confidence_threshold`: Threshold mínimo para detecção (padrão: 0.25)

**Output**: Lista de bounding boxes `[x1, y1, x2, y2]` com confiança

---

### 2. Nudity Analyzer (`nudity_analyzer.py`)

**Responsabilidade**: Analisar nudez baseado em scores anatômicos, não strings.

**Tecnologia**: NudeNet

**Justificativa Técnica**:
- **Nunca executa NudeNet em imagem full-frame**: Apenas em ROIs (regiões de pessoas)
- **Decisão baseada em score anatômico**: Não usa regras frágeis como string matching
- **Agrupamento espacial**: Partes anatômicas próximas são agrupadas
- **Avaliação multi-critério**:
  - Tipo anatômico detectado
  - Score do modelo
  - Número de partes correlatas

**Regras de Decisão**:
- Uma única detecção isolada ≠ nudez
- Duas ou mais partes anatômicas coerentes ≈ nudez provável
- Tipos críticos (genitália, ânus) têm thresholds mais baixos

**Thresholds por Tipo Anatômico**:
```python
GENITALIA: base_threshold * 0.6  # Mais sensível
ANUS: base_threshold * 0.6       # Mais sensível
NIPPLE: base_threshold * 0.8
BREAST: base_threshold * 0.9     # Menos sensível
BUTTOCKS: base_threshold * 0.85
```

**Output**: Resultado de avaliação com:
- `is_nudity`: bool
- `confidence`: float
- `groups`: Lista de grupos de partes anatômicas
- `parts`: Lista de todas as partes detectadas

---

### 3. Severity Classifier (`severity_classifier.py`)

**Responsabilidade**: Classificar severidade hierarquicamente.

**Níveis de Severidade**:
- **SAFE**: Sem conteúdo sensível
- **SUGGESTIVE**: Conteúdo sugestivo (ex: seios sem mamilos)
- **NSFW**: Conteúdo explícito (genitália, ânus)

**Regras de Classificação**:

1. **Genitália ou ânus → sempre NSFW**
   - Máxima severidade, independente de contexto

2. **Seios sem mamilos → SUGGESTIVE**
   - Pode ser NSFW se score muito alto (≥ 0.85)

3. **Mamilos → NSFW**
   - Conteúdo explícito

4. **Nádegas → depende do contexto**
   - Combinado com outras partes ou score alto → NSFW
   - Isolado → SUGGESTIVE

5. **Múltiplas partes correlatas → aumenta severidade**
   - 2+ tipos anatômicos → NSFW

**Justificativa Técnica**:
- Classificação hierárquica permite granularidade na moderação
- Diferentes níveis de ação podem ser tomados por severidade
- Evita falsos positivos em conteúdo sugestivo mas não explícito

---

### 4. Temporal Aggregator (`temporal_aggregator.py`)

**Responsabilidade**: Agregar detecções ao longo do tempo (vídeo).

**Justificativa Técnica**:
- Um único frame NSFW não é suficiente para confirmar nudez
- Filtra falsos positivos temporais
- Confirma nudez apenas com consistência entre múltiplos frames

**Critérios de Confirmação**:

1. **Frames Consecutivos**:
   - Nudez confirmada se aparecer em N frames consecutivos (padrão: 3)

2. **Score Acumulado**:
   - Nudez confirmada se score acumulado ≥ threshold (padrão: 2.0)

3. **Janela Deslizante**:
   - Nudez confirmada se ≥ 60% dos frames na janela são NSFW

**Parâmetros**:
- `min_consecutive_frames`: Mínimo de frames consecutivos (padrão: 3)
- `min_accumulated_score`: Score acumulado mínimo (padrão: 2.0)
- `window_size`: Tamanho da janela deslizante (padrão: 10)

---

### 5. Observability (`observability.py`)

**Responsabilidade**: Logs estruturados para inspeção completa do pipeline.

**Formato**: JSON estruturado

**Informações Registradas**:
- Pessoas detectadas (bbox, confiança)
- Partes anatômicas detectadas (tipo, score, bbox)
- Scores e confianças
- Decisão final (severidade, razão)
- Estatísticas temporais (vídeo)

**Modo Debug**:
- Logs detalhados de cada estágio
- Todas as detecções intermediárias
- Justificativas de decisões

**Justificativa Técnica**:
- Facilita debugging e auditoria
- Permite análise de performance
- Suporta compliance e transparência

---

## Pipeline Principal (`nudity_pipeline.py`)

**Responsabilidade**: Orquestrar todos os estágios.

**Fluxo de Processamento**:

1. **Carrega imagem**
2. **Estágio 1**: Detecta humanos
   - Se nenhum humano → retorna SAFE
3. **Estágio 2**: Para cada pessoa detectada:
   - Extrai ROI
   - Analisa nudez na ROI
   - Agrupa partes por proximidade
4. **Estágio 3**: Classifica severidade
5. **Estágio 4** (vídeo): Agrega temporalmente
6. **Observabilidade**: Registra logs

---

## Estratégia de Thresholds

### Thresholds por Classe Anatômica

| Tipo Anatômico | Threshold Relativo | Justificativa |
|----------------|-------------------|---------------|
| Genitália | 0.6x base | Máxima severidade, reduz falsos negativos |
| Ânus | 0.6x base | Máxima severidade, reduz falsos negativos |
| Mamilos | 0.8x base | Alta severidade |
| Nádegas | 0.85x base | Severidade média-alta |
| Seios | 0.9x base | Menos sensível, pode ser sugestivo |

### Threshold Base Recomendado

- **Padrão**: 0.30
- **Conservador** (menos falsos positivos): 0.40
- **Sensível** (menos falsos negativos): 0.20

---

## Pós-processamento Visual

### Aplicação de Blur

**Regras**:
- Nunca tenta "corrigir" falsos positivos apenas na decisão lógica
- Em caso de dúvida, aplica blur nas regiões suspeitas
- Expande bounding boxes com margem adaptativa baseada no tamanho da região

**Parâmetros**:
- `intensidade_blur`: Intensidade do blur (ímpar, padrão: 75)
- `margem_percentual`: Margem de expansão (padrão: 40%)
- `margem_minima`: Margem mínima absoluta (30 pixels)

**Algoritmo**:
1. Para cada parte anatômica detectada:
   - Obtém bbox absoluto
   - Expande com margem adaptativa
   - Calcula intensidade de blur baseada no tamanho
   - Aplica blur gaussiano múltiplas vezes
2. Salva imagem processada

---

## Considerações de Performance

### Otimizações Implementadas

1. **Detecção de humanos primeiro**: Reduz processamento desnecessário
2. **Processamento apenas em ROIs**: NudeNet executa apenas em regiões relevantes
3. **Modelo YOLO configurável**: Pode usar modelo menor ('n') para velocidade
4. **Agregação temporal eficiente**: Janela deslizante com deque

### Escalabilidade

- **Processamento paralelo**: Pode processar múltiplas imagens em paralelo
- **Batch processing**: Suporta processamento em lote
- **Streaming**: Agregação temporal permite processamento de vídeo em streaming

### Limitações Conhecidas

- YOLOv8 requer GPU para melhor performance (CPU funciona mas é mais lento)
- NudeNet é relativamente pesado (pode ser otimizado com quantização)
- Processamento de vídeo pode ser lento para vídeos longos

---

## Extensibilidade

### Adicionar Novos Modelos

O sistema foi projetado para ser extensível:

1. **Novo detector de humanos**: Implementar interface similar a `HumanDetector`
2. **Novo analisador de nudez**: Implementar interface similar a `NudityAnalyzer`
3. **Novos classificadores**: Adicionar regras em `SeverityClassifier`

### Exemplo: Adicionar YOLO-NAS

```python
class HumanDetectorYOLONAS(HumanDetector):
    def __init__(self, ...):
        # Carrega YOLO-NAS ao invés de YOLOv8
        ...
```

---

## Critérios de Sucesso

O sistema deve:

✅ **Detectar nudez humana real mesmo parcialmente visível**
- Agrupamento espacial captura partes correlatas
- Thresholds adaptativos por tipo anatômico

✅ **Ignorar objetos, bonecos e padrões de textura**
- Detecção de humanos primeiro filtra objetos
- Análise apenas em bounding boxes de pessoas

✅ **Priorizar segurança visual em casos ambíguos**
- Em dúvida, aplica blur
- Classificação hierárquica permite ação apropriada

✅ **Ser extensível para novos modelos no futuro**
- Arquitetura modular
- Interfaces bem definidas

---

## Referências Técnicas

- **YOLOv8**: https://github.com/ultralytics/ultralytics
- **NudeNet**: https://github.com/notAI-tech/NudeNet
- **COCO Dataset**: Classes de objetos padrão (person = ID 0)

---

## Autores

Sistema projetado e implementado conforme especificação de requisitos para detecção robusta de nudez em imagens e vídeos.

