# 🔍 Detector de Nudez - Pipeline Multiestágio

## 📋 Descrição

Sistema avançado de detecção de conteúdo NSFW (Not Safe For Work) em imagens e vídeos, implementado com uma arquitetura multiestágio baseada em deep learning. O projeto utiliza uma abordagem em cascata que combina detecção de objetos humanos (YOLOv8) com análise especializada de nudez (NudeNet), resultando em alta precisão e baixa taxa de falsos positivos.

### Características Principais

- **Arquitetura Multiestágio**: Pipeline de 4 estágios que primeiro identifica humanos antes de analisar conteúdo sensível, reduzindo processamento desnecessário e melhorando a precisão
- **Classificação Hierárquica**: Sistema de classificação em três níveis (SAFE, SUGGESTIVE, NSFW) para avaliação precisa do conteúdo
- **Processamento de Vídeo**: Suporte completo para análise de vídeos com agregação temporal, garantindo consistência entre frames
- **Aplicação de Blur Automático**: Capacidade de aplicar blur automático em áreas detectadas, preservando o áudio original em vídeos
- **Observabilidade**: Sistema de logs estruturados para debug e monitoramento do processo de detecção
- **API Simples**: Interface Python intuitiva e fácil de integrar em outros projetos

### Casos de Uso

- Moderação de conteúdo em plataformas de mídia social
- Filtragem automática de conteúdo em sistemas de upload
- Análise de conformidade em ambientes corporativos
- Sistemas de segurança e monitoramento
- Aplicações de parental control

## 📁 Estrutura do Projeto

```
deteccao_nudez/
├── src/                    # Código fonte principal
│   ├── detector_nudez_v2.py      # Interface principal (recomendado)
│   ├── detector_nudez.py         # Implementação legada
│   ├── nudity_pipeline.py        # Pipeline completo
│   ├── human_detector.py         # Estágio 1: Detecção de humanos
│   ├── nudity_analyzer.py        # Estágio 2: Análise de nudez
│   ├── severity_classifier.py    # Estágio 3: Classificação
│   ├── temporal_aggregator.py    # Estágio 4: Agregação temporal
│   └── observability.py          # Sistema de logs
├── examples/               # Scripts de exemplo
│   ├── exemplo_uso.py
│   ├── exemplo_video.py
│   └── ...
├── docs/                   # Documentação
│   ├── README.md           # Este arquivo (link simbólico ou cópia)
│   ├── README_V2.md        # Documentação v2.0
│   ├── ARCHITECTURE.md     # Arquitetura detalhada
│   └── IMPLEMENTACAO_VIDEO_BLUR.md
├── data/                   # Dados de teste
│   ├── videos/             # Vídeos de teste
│   └── resultado_video.json
├── models/                 # Modelos pré-treinados
│   └── yolov8n.pt
└── requirements.txt        # Dependências
```

## 🚀 Início Rápido

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Instalar FFmpeg (necessário para processamento de vídeo)
sudo apt install ffmpeg  # Linux
# ou
brew install ffmpeg      # macOS
```

### Uso Básico

```bash
# Processar uma imagem
python -m src.detector_nudez_v2 foto.jpg

# Processar imagem com blur
python -m src.detector_nudez_v2 --blur foto.jpg

# Processar vídeo completo com blur
python examples/exemplo_video_com_blur.py data/videos/video.mp4
```

## 📖 Documentação Completa

- **Documentação Principal**: Veja [docs/README_V2.md](docs/README_V2.md)
- **Arquitetura**: Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Implementação de Vídeo**: Veja [docs/IMPLEMENTACAO_VIDEO_BLUR.md](docs/IMPLEMENTACAO_VIDEO_BLUR.md)

## 🎯 Funcionalidades

- ✅ Detecção de nudez em imagens
- ✅ Processamento de vídeo completo com blur
- ✅ Pipeline multiestágio robusto
- ✅ Classificação hierárquica (SAFE, SUGGESTIVE, NSFW)
- ✅ Preservação de áudio original em vídeos
- ✅ Logs estruturados para debug

## 📝 Exemplos

Todos os exemplos estão em `examples/`:

```bash
# Exemplo básico
python examples/exemplo_uso.py

# Processar vídeo
python examples/exemplo_video_com_blur.py data/videos/video.mp4

# Descrição textual de detecção
python examples/exemplo_descricao_nudez.py imagem.jpg
```

## 🔧 Estrutura Técnica

O sistema usa um pipeline de 4 estágios:

1. **Detecção de Humanos** (YOLOv8) - Filtra objetos não-humanos
2. **Análise de Nudez** (NudeNet) - Detecta partes anatômicas em ROIs
3. **Classificação Hierárquica** - Classifica severidade
4. **Agregação Temporal** (vídeo) - Confirma detecções em múltiplos frames

Veja `docs/ARCHITECTURE.md` para detalhes completos.
