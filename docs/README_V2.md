# 🔍 Detector de Nudez v2.0 - Pipeline Multiestágio

Sistema robusto de detecção de nudez em imagens e vídeos implementando arquitetura **pipeline multiestágio** para minimizar falsos positivos e falsos negativos.

## 🏗️ Arquitetura

O sistema implementa um pipeline de 4 estágios:

1. **Detecção de Humanos** (YOLOv8) - Detecta apenas pessoas na imagem
2. **Análise de Nudez** (NudeNet) - Analisa nudez apenas em bounding boxes de pessoas
3. **Classificação Hierárquica** - Classifica em SAFE, SUGGESTIVE ou NSFW
4. **Agregação Temporal** (vídeo) - Confirma nudez apenas com consistência entre frames

Veja [ARCHITECTURE.md](ARCHITECTURE.md) para documentação completa da arquitetura.

## 📋 Requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)
- **FFmpeg** (para processamento de vídeos)
  - Instalar: `sudo apt install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS)

## 🚀 Instalação

1. **Navegue até a pasta do projeto:**
```bash
cd deteccao_nudez
```

2. **Instale as dependências:**
```bash
pip3 install -r requirements.txt
# ou
python3 -m pip install -r requirements.txt
```

**Nota:** Na primeira execução, os modelos serão baixados automaticamente:
- YOLOv8 (Ultralytics) - ~6MB (modelo nano)
- NudeNet - ~100MB

## 💻 Como Usar

### Usando o novo pipeline (recomendado)

```bash
# Detectar uma imagem
python3 detector_nudez_v2.py foto.jpg

# Detectar com blur
python3 detector_nudez_v2.py --blur foto.jpg

# Modo debug (mostra todos os estágios)
python3 detector_nudez_v2.py --debug foto.jpg

# Processar vídeo
python3 detector_nudez_v2.py --video video.mp4

# Ajustar threshold
python3 detector_nudez_v2.py --threshold 0.2 foto.jpg
```

### Usando implementação legada (fallback)

```bash
python3 detector_nudez_v2.py --legacy foto.jpg
```

## 📝 Opções Disponíveis

```
--blur, -b              Aplica blur nas áreas detectadas
--intensidade, -i NUM   Intensidade do blur (ímpar, padrão: 75)
--margem, -m NUM        Margem de expansão do blur em % (0-100, padrão: 40)
--saida, -o CAMINHO     Pasta para salvar imagens processadas
--threshold, -t NUM     Threshold de confiança (0.0-1.0, padrão: 0.30)
--debug, -d             Mostra todas as detecções (modo debug)
--video, -v             Processa um vídeo (extrai frames e detecta nudez)
--intervalo NUM         Intervalo entre frames em segundos (padrão: 1.0)
--legacy                Usa implementação antiga (não recomendado)
--help, -h              Mostra ajuda
```

## 🎯 Características Principais

### ✅ Minimiza Falsos Positivos

- **Detecção de humanos primeiro**: Ignora objetos, bonecos e padrões de textura
- **Análise apenas em ROIs**: NudeNet executa apenas em regiões de pessoas
- **Agrupamento espacial**: Uma única detecção isolada não é suficiente
- **Agregação temporal**: Para vídeo, confirma apenas com múltiplos frames

### ✅ Minimiza Falsos Negativos

- **Thresholds adaptativos**: Tipos críticos (genitália, ânus) têm thresholds mais baixos
- **Múltiplas partes correlatas**: Detecta nudez mesmo parcialmente visível
- **Classificação hierárquica**: Diferentes níveis de severidade

### ✅ Observabilidade

- **Logs estruturados**: JSON completo de cada estágio
- **Modo debug**: Inspeção completa do pipeline
- **Estatísticas temporais**: Para análise de vídeo

## 📊 Classificação de Severidade

O sistema classifica cada imagem/frame em:

- **SAFE**: Sem conteúdo sensível
- **SUGGESTIVE**: Conteúdo sugestivo (ex: seios sem mamilos)
- **NSFW**: Conteúdo explícito (genitália, ânus)

## 🔧 Estrutura do Projeto

```
deteccao_nudez/
├── detector_nudez_v2.py      # Interface principal (novo)
├── detector_nudez.py         # Implementação legada
├── nudity_pipeline.py        # Pipeline principal
├── human_detector.py         # Estágio 1: Detecção de humanos
├── nudity_analyzer.py        # Estágio 2: Análise de nudez
├── severity_classifier.py    # Estágio 3: Classificação
├── temporal_aggregator.py     # Estágio 4: Agregação temporal
├── observability.py          # Sistema de logs
├── ARCHITECTURE.md           # Documentação da arquitetura
├── README_V2.md              # Este arquivo
└── requirements.txt          # Dependências
```

## 📖 Exemplos

### Exemplo 1: Detectar imagem com debug

```bash
python3 detector_nudez_v2.py --debug foto.jpg
```

Saída mostra:
- Humanos detectados
- Partes anatômicas detectadas
- Agrupamento espacial
- Classificação de severidade
- Decisão final

### Exemplo 2: Processar vídeo com blur

```bash
python3 detector_nudez_v2.py --video --blur video.mp4
```

- Extrai frames a cada 1 segundo
- Detecta nudez em cada frame
- Agrega temporalmente
- Aplica blur nos frames NSFW confirmados
- Salva frames editados em pasta separada

### Exemplo 3: Threshold conservador

```bash
python3 detector_nudez_v2.py --threshold 0.4 foto.jpg
```

Reduz falsos positivos (menos sensível).

### Exemplo 4: Threshold sensível

```bash
python3 detector_nudez_v2.py --threshold 0.2 foto.jpg
```

Reduz falsos negativos (mais sensível).

## 🐛 Troubleshooting

### Erro: "YOLOv8 não está instalado"

```bash
pip3 install ultralytics
```

### Erro: "NudeNet não está instalado"

```bash
pip3 install nudenet
```

### Erro: "FFmpeg não encontrado"

```bash
# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### Performance lenta

- Use modelo YOLO menor (padrão: 'n' = nano)
- Processe imagens em batch
- Use GPU se disponível (YOLOv8 detecta automaticamente)

## 🔬 Modo Debug

O modo debug (`--debug`) mostra:

1. **Estágio 1**: Pessoas detectadas com bbox e confiança
2. **Estágio 2**: Partes anatômicas detectadas, agrupamento espacial
3. **Estágio 3**: Classificação de severidade com justificativa
4. **Estágio 4** (vídeo): Estatísticas temporais, frames consecutivos

## 📈 Performance

### Tempos Médios (CPU, modelo nano)

- **Imagem única**: ~2-3 segundos
- **Frame de vídeo**: ~2-3 segundos
- **Vídeo 1 minuto** (60 frames): ~2-3 minutos

### Otimizações

- Use GPU para YOLOv8 (detecção automática)
- Processe múltiplas imagens em paralelo
- Ajuste intervalo de frames em vídeo (padrão: 1 segundo)

## 🔒 Privacidade e Segurança

- **Processamento local**: Tudo roda localmente, sem envio de dados
- **Blur preserva privacidade**: Aplica blur apenas em regiões detectadas
- **Logs opcionais**: Logs estruturados apenas em modo debug

## 📚 Documentação Adicional

- [ARCHITECTURE.md](ARCHITECTURE.md) - Documentação completa da arquitetura
- [requirements.txt](requirements.txt) - Lista de dependências

## 🤝 Contribuindo

O sistema foi projetado para ser extensível:

- Adicione novos detectores de humanos
- Adicione novos analisadores de nudez
- Estenda classificador de severidade
- Melhore agregação temporal

Veja [ARCHITECTURE.md](ARCHITECTURE.md) para detalhes de extensibilidade.

## 📄 Licença

Este projeto é fornecido como está, para uso educacional e de pesquisa.

## 🙏 Créditos

- **YOLOv8**: Ultralytics (https://github.com/ultralytics/ultralytics)
- **NudeNet**: notAI-tech (https://github.com/notAI-tech/NudeNet)

---

**Versão**: 2.0  
**Última atualização**: 2024

