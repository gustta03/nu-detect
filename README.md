# 🔍 Detector de Nudez em Imagens

Aplicação Python para detectar conteúdo NSFW (Not Safe For Work) em imagens usando a biblioteca **NudeNet**.

## 📋 Requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)
- **FFmpeg** (para processamento de vídeos)
  - Instalar: `sudo apt install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS)

**Nota:** Em sistemas Linux, use `python3` ao invés de `python` nos comandos.

## 🚀 Instalação

1. **Clone ou navegue até a pasta do projeto:**
```bash
cd deteccao_nudez
```

2. **Instale as dependências:**
```bash
pip3 install -r requirements.txt
# ou
python3 -m pip install -r requirements.txt
```

**Nota:** Na primeira execução, o NudeNet baixará automaticamente os modelos necessários (pode levar alguns minutos).

## 🧪 Teste Rápido

Para testar rapidamente com a imagem de exemplo incluída (`image.png`):

```bash
# Usar o script de exemplo (recomendado)
python3 exemplo_uso.py

# Ou usar diretamente o detector
python3 detector_nudez.py image.png
python3 detector_nudez.py --blur image.png
```

## 💻 Como Usar

### Detectar uma única imagem:
```bash
python3 detector_nudez.py caminho/para/imagem.jpg
```

### Detectar todas as imagens de uma pasta:
```bash
python3 detector_nudez.py caminho/para/pasta/
```

### Aplicar blur nas áreas detectadas:
```bash
python3 detector_nudez.py --blur caminho/para/imagem.jpg
```

### Processar vídeo (extrair frames, detectar nudez e aplicar blur):
```bash
python3 detector_nudez.py --video caminho/para/video.mp4
python3 detector_nudez.py --video --intervalo 2.0 video.mp4  # Frame a cada 2 segundos
```
**Nota:** Os frames com conteúdo NSFW são automaticamente editados com blur e salvos em uma pasta separada.

## 📝 Exemplos

```bash
# Detectar uma foto específica
python3 detector_nudez.py foto.jpg

# Detectar e aplicar blur automaticamente
python3 detector_nudez.py --blur foto.jpg

# Aplicar blur com intensidade personalizada (ímpar)
python3 detector_nudez.py --blur -i 75 foto.jpg

# Detectar todas as imagens de uma pasta e aplicar blur
python3 detector_nudez.py --blur ./minhas_fotos/

# Salvar imagens processadas em pasta específica
python3 detector_nudez.py --blur -o ./imagens_processadas/ ./minhas_fotos/

# Usar caminho absoluto
python3 detector_nudez.py /home/usuario/imagens/teste.png

# Testar com a imagem de exemplo incluída
python3 detector_nudez.py image.png
python3 detector_nudez.py --blur image.png

# Ou usar o script de exemplo
python3 exemplo_uso.py

# Processar vídeo (extrair frames, detectar nudez e aplicar blur)
python3 detector_nudez.py --video video.mp4
python3 detector_nudez.py --video --intervalo 2.0 video.mp4
python3 exemplo_video.py video.mp4 1.0
# Os frames com NSFW são automaticamente editados com blur

# Ver todas as opções disponíveis
python3 detector_nudez.py --help
```

## 🎨 Opções de Blur

- `--blur` ou `-b`: Ativa a aplicação de blur nas áreas detectadas
- `--intensidade NUM` ou `-i NUM`: Define a intensidade do blur (deve ser ímpar, padrão: 51)
  - Valores maiores = blur mais intenso
  - Valores menores = blur mais suave
- `--saida CAMINHO` ou `-o CAMINHO`: Define pasta para salvar imagens processadas
  - Se não especificado, salva na mesma pasta com prefixo `blur_`

## 📊 Formato de Saída

### Para Imagens:
- ✅ Se a imagem é segura (sem conteúdo NSFW)
- ⚠️ Se foi detectado conteúdo NSFW, com:
  - Nível de confiança (porcentagem)
  - Tipo de detecção (partes do corpo detectadas)
  - Número total de detecções
- ✨ Se o blur foi aplicado:
  - Caminho da imagem processada
  - Número de áreas com blur aplicado

### Para Vídeos:
- Duração total do vídeo
- Total de frames processados
- Intervalo entre frames
- **Lista de timestamps onde há conteúdo NSFW:**
  - Timestamp formatado (HH:MM:SS)
  - Timestamp em segundos
  - Nível de confiança
  - Número de detecções
  - Classes detectadas em cada cena

## 🔧 Funcionalidades

- ✅ Detecção de múltiplos tipos de conteúdo NSFW
- ✅ Suporte a várias imagens de uma vez (pasta)
- ✅ **Processamento de vídeos (extração de frames com FFmpeg)**
- ✅ **Detecção frame a frame com timestamps precisos**
- ✅ **Aplicação automática de blur nas áreas detectadas**
- ✅ **Intensidade de blur configurável**
- ✅ **Pasta de saída personalizada para imagens processadas**
- ✅ Formato de saída claro e informativo
- ✅ Tratamento de erros robusto
- ✅ Suporte a formatos: JPG, PNG, BMP, WEBP
- ✅ Suporte a vídeos: MP4, AVI, MKV, MOV (via FFmpeg)

## 📦 Dependências

- **nudenet** (>=3.0.0): Biblioteca principal para detecção NSFW
- **tensorflow** (>=2.8.0): Framework de machine learning (requerido pelo nudenet)
- **Pillow** (>=10.0.0): Processamento de imagens
- **opencv-python** (>=4.8.0): Processamento avançado de imagens
- **numpy** (>=1.24.0): Operações numéricas

**Nota:** O TensorFlow é uma dependência grande (~600MB). A primeira instalação pode levar alguns minutos.

## ⚠️ Avisos

- Esta ferramenta é para fins educacionais e de moderação de conteúdo
- A precisão pode variar dependendo da qualidade da imagem
- Use com responsabilidade e ética
- Sempre revise manualmente resultados importantes

## 🐛 Solução de Problemas

### Erro: "Biblioteca nudenet não encontrada"
```bash
pip3 install -r requirements.txt
# ou
python3 -m pip install -r requirements.txt
```

### Erro: "command not found: python"
Em sistemas Linux, use `python3` ao invés de `python`:
```bash
python3 detector_nudez.py image.png
python3 exemplo_uso.py
```

### Erro ao processar imagem
- Verifique se o arquivo é uma imagem válida
- Verifique se o caminho está correto
- Certifique-se de que a imagem não está corrompida

### Modelo não baixa automaticamente
O NudeNet baixa os modelos na primeira execução. Se houver problemas:
- Verifique sua conexão com a internet
- O download pode levar alguns minutos

### Erro: "FFmpeg não encontrado"
Para processar vídeos, é necessário instalar o FFmpeg:
```bash
# Linux (Debian/Ubuntu)
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verificar instalação
ffmpeg -version
```

### Vídeos muito longos (3-5 horas)
Para vídeos longos, recomenda-se usar um intervalo maior entre frames:
```bash
# Processa 1 frame a cada 5 segundos (mais rápido)
python3 detector_nudez.py --video --intervalo 5.0 video_longo.mp4

# Processa 1 frame a cada 10 segundos (muito mais rápido)
python3 detector_nudez.py --video --intervalo 10.0 video_longo.mp4
```

## 📄 Licença

Este projeto é fornecido como está, para fins educacionais.

