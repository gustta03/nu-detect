# 📋 Guia de Comandos - Detector de Nudez

Lista completa de comandos disponíveis e o que cada um faz.

## 📦 Instalação

### Instalar Dependências
```bash
pip install -r requirements.txt
```
**O que faz:** Instala todas as bibliotecas Python necessárias (nudenet, ultralytics, opencv, etc.)

### Instalar FFmpeg (necessário para vídeos)
```bash
# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```
**O que faz:** Instala o FFmpeg, necessário para processar vídeos (extrair frames, reconstruir vídeo com áudio)

---

## 🖼️ Processamento de Imagens

### 1. Detectar Nudez em Imagem (Script Principal)
```bash
python3 -m src.detector_nudez_v2 imagem.jpg
```
**O que faz:** Analisa uma imagem e mostra se há conteúdo NSFW detectado, com informações de severidade (SAFE, SUGGESTIVE, NSFW)

### 2. Detectar Nudez com Blur Automático
```bash
python3 -m src.detector_nudez_v2 --blur imagem.jpg
```
**O que faz:** Detecta nudez e aplica blur automático nas áreas detectadas, salvando uma nova imagem com prefixo `blur_`

### 3. Detectar com Threshold Personalizado
```bash
python3 -m src.detector_nudez_v2 --threshold 0.2 imagem.jpg
```
**O que faz:** Usa um threshold de confiança personalizado (0.0-1.0). Valores menores = mais sensível

### 4. Detectar com Modo Debug
```bash
python3 -m src.detector_nudez_v2 --debug imagem.jpg
```
**O que faz:** Mostra todas as detecções detalhadas, incluindo partes não-NSFW (útil para debug)

### 5. Detectar em Pasta Inteira
```bash
python3 -m src.detector_nudez_v2 pasta_imagens/
```
**O que faz:** Processa todas as imagens na pasta (jpg, png, bmp, webp) e mostra resumo

### 6. Detectar com Blur e Salvar em Pasta Específica
```bash
python3 -m src.detector_nudez_v2 --blur --saida ./resultados/ imagem.jpg
```
**O que faz:** Aplica blur e salva a imagem processada na pasta `./resultados/`

### 7. Detectar com Blur Intenso
```bash
python3 -m src.detector_nudez_v2 --blur --intensidade 95 imagem.jpg
```
**O que faz:** Aplica blur com intensidade 95 (ímpar, padrão: 75). Valores maiores = blur mais forte

### 8. Detectar com Margem de Blur Personalizada
```bash
python3 -m src.detector_nudez_v2 --blur --margem 50 imagem.jpg
```
**O que faz:** Expande a área de blur em 50% além do bounding box detectado (padrão: 40%)

### 9. Exemplo Básico de Uso
```bash
python3 examples/exemplo_uso.py
```
**O que faz:** Script de exemplo que detecta nudez em `image.png` (deve estar na mesma pasta) e aplica blur se necessário

### 10. Obter Descrição Textual de Detecção
```bash
python3 examples/exemplo_descricao_nudez.py imagem.jpg
```
**O que faz:** Retorna apenas uma descrição textual da detecção (sem processar frames), útil para APIs

---

## 🎬 Processamento de Vídeos

### 11. ⭐ Processar Vídeo Completo com Blur (RETORNA MP4 EDITADO - NÃO FRAMES)
```bash
python3 examples/exemplo_video_com_blur.py video.mp4 video_editado.mp4
```
**O que faz:** 
- ✅ Processa TODOS os frames do vídeo
- ✅ Aplica blur onde necessário
- ✅ Reconstrói vídeo MP4 completo com áudio original preservado
- ✅ Salva em `video_editado.mp4` (ou nome especificado)
- ❌ **NÃO salva frames individuais** (apenas o vídeo final)
- ✅ **Modo conservador ativado**: não espera agregação temporal para começar o blur e considera 1 parte sensível (ex: `BREAST`) suficiente para acionar blur

**Exemplo:**
```bash
python3 examples/exemplo_video_com_blur.py data/videos/curto.mp4 video_editado.mp4
```

### 12. Processar Vídeo com Nome Automático
```bash
python3 examples/exemplo_video_com_blur.py video.mp4
```
**O que faz:** Processa vídeo e salva automaticamente como `video_editado.mp4` na mesma pasta do vídeo original

### 13. Processar Vídeo Frame a Frame (Script Principal)
```bash
python3 -m src.detector_nudez_v2 --video video.mp4
```
**O que faz:** Extrai frames do vídeo e detecta nudez em cada frame, mostrando timestamps onde há conteúdo NSFW

### 14. Processar Vídeo com Intervalo Específico
```bash
python3 -m src.detector_nudez_v2 --video --intervalo 2.0 video.mp4
```
**O que faz:** Analisa 1 frame a cada 2 segundos (útil para vídeos longos, mais rápido)

### 15. Processar Vídeo com Blur nos Frames
```bash
python3 -m src.detector_nudez_v2 --video --blur video.mp4
```
**O que faz:** Detecta nudez e salva frames editados com blur em pasta separada (não reconstrói vídeo completo)

### 16. Processar Vídeo (Exemplo Simples)
```bash
python3 examples/exemplo_video.py video.mp4 1.0
```
**O que faz:** Versão simplificada que processa vídeo com intervalo de 1 segundo e aplica blur automaticamente

### 17. Obter Descrição Textual de Vídeo
```bash
python3 examples/exemplo_descricao_video.py video.mp4
```
**O que faz:** Analisa vídeo e retorna apenas descrição textual dos timestamps onde há nudez (sem processar frames)

---

## ⚙️ Opções Avançadas

### 18. Usar Implementação Legada
```bash
python3 -m src.detector_nudez_v2 --legacy imagem.jpg
```
**O que faz:** Usa a versão antiga do detector (sem pipeline multiestágio, não recomendado)

### 19. Ver Ajuda Completa
```bash
python3 -m src.detector_nudez_v2 --help
```
**O que faz:** Mostra todas as opções disponíveis e exemplos de uso

### 20. Combinar Múltiplas Opções
```bash
python3 -m src.detector_nudez_v2 --blur --threshold 0.25 --debug --intensidade 85 --margem 45 imagem.jpg
```
**O que faz:** Combina múltiplas opções: blur, threshold personalizado, modo debug, blur intenso e margem maior

---

## 📊 Resumo dos Parâmetros

| Parâmetro | Descrição | Valores |
|-----------|-----------|---------|
| `--blur, -b` | Aplica blur nas áreas detectadas | Flag (sem valor) |
| `--threshold, -t` | Threshold de confiança | 0.0 a 1.0 (padrão: 0.30) |
| `--debug, -d` | Modo debug detalhado | Flag |
| `--intensidade, -i` | Intensidade do blur | Ímpar (padrão: 75) |
| `--margem, -m` | Margem de expansão do blur | 0-100% (padrão: 40%) |
| `--saida, -o` | Pasta de saída | Caminho |
| `--video, -v` | Processa vídeo | Flag |
| `--intervalo` | Intervalo entre frames (vídeo) | Segundos (padrão: 1.0) |
| `--legacy` | Usa implementação antiga | Flag |

---

## 🎯 Casos de Uso Comuns

### Moderação de Upload
```bash
python3 -m src.detector_nudez_v2 --blur --threshold 0.2 upload.jpg
```

### Análise de Vídeo Completo
```bash
python3 examples/exemplo_video_com_blur.py video.mp4 video_seguro.mp4
```

### Debug de Detecções
```bash
python3 -m src.detector_nudez_v2 --debug --threshold 0.15 imagem.jpg
```

### Processamento em Lote
```bash
python3 -m src.detector_nudez_v2 --blur --saida ./processados/ pasta_imagens/
```

---

## 📝 Notas Importantes

1. **Primeira execução:** O modelo YOLOv8 será baixado automaticamente (~6MB)
2. **Vídeos longos:** Use `--intervalo` maior para processar mais rápido
3. **Blur em vídeos:** `exemplo_video_com_blur.py` reconstrói vídeo completo; `--video --blur` apenas salva frames
4. **Performance:** Processamento de vídeo pode levar tempo dependendo do tamanho e duração
5. **FFmpeg:** Necessário apenas para processamento de vídeos

