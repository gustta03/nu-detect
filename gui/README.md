# GUI - Detector de Nudez v2.0

Interface gráfica moderna para o Detector de Nudez usando CustomTkinter.

## Executar GUI

### Modo Desenvolvimento

```bash
# Instalar dependências (incluindo customtkinter)
pip install -r ../requirements.txt

# Executar GUI
python gui_main.py
```

### Criar Executável

```bash
# Instalar PyInstaller
pip install pyinstaller

# Criar executável (Linux/Windows)
pyinstaller detector_nudez.spec

# Executável estará em: dist/DetectorNudez (Linux) ou dist/DetectorNudez.exe (Windows)
```

## Funcionalidades

- Seleção de arquivos (imagens e vídeos)
- Configurações ajustáveis:
  - Threshold de detecção (0.0 - 1.0)
  - Intensidade do blur (25 - 150)
  - Margem do blur (0% - 100%)
  - Modo conservador (mais sensível)
- Processamento assíncrono (não trava a interface)
- Barra de progresso
- Logs em tempo real
- Exibição de resultados
- Salvar resultados em JSON

## Interface

A GUI usa **CustomTkinter** para um visual moderno e dark theme por padrão.

### Componentes:

1. **Seleção de Arquivo**: Botão para escolher imagem ou vídeo
2. **Configurações**: Sliders para ajustar parâmetros
3. **Botões de Ação**: Processar e Parar
4. **Progresso**: Barra de progresso e status
5. **Logs**: Área de texto com logs do processamento
6. **Resultados**: Exibição dos resultados com cores (verde/amarelo/vermelho)

## Requisitos

### Dependências do Sistema

**Linux** (instalar antes das dependências Python):
- **Ubuntu/Debian**: `sudo apt install python3-tk`
- **Fedora/RHEL/CentOS**: `sudo dnf install python3-tkinter`
- **Arch/Manjaro**: `sudo pacman -S tk`

Ou use o script de instalação:
```bash
./install_gui_deps.sh
```

**Windows/macOS**: Tkinter geralmente já vem pré-instalado com Python.

### Dependências Python

- Python 3.7+
- customtkinter >= 5.2.0
- Todas as dependências do projeto (ver requirements.txt)

Instalar com:
```bash
pip install -r requirements.txt
```

## Tamanho do Executável

O executável gerado será grande (300-800MB) devido a:
- TensorFlow (~500MB)
- OpenCV (~100MB)
- Modelos ML (YOLOv8, NudeNet)

**Dica**: Para reduzir tamanho, pode-se:
- Fazer download dos modelos na primeira execução
- Usar TensorFlow Lite
- Comprimir com UPX (já habilitado no .spec)

## Solução de Problemas

### GUI não inicia

- Verifique se customtkinter está instalado: `pip install customtkinter`
- Verifique se todas as dependências estão instaladas: `pip install -r requirements.txt`

### Executável muito grande

- Isso é esperado devido às dependências ML
- Considere distribuir como instalar ou usar Docker

### Erro ao criar executável

- Verifique se PyInstaller está atualizado: `pip install --upgrade pyinstaller`
- Limpe builds anteriores: `rm -rf build dist __pycache__`
- Tente criar novamente

## Notas

- A GUI processa arquivos de forma assíncrona (não trava)
- Para parar processamento em andamento, feche e reabra a aplicação
- Modelos são carregados na inicialização (pode demorar alguns segundos)
- Resultados podem ser salvos em formato JSON

