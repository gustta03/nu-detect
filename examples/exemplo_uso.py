
"""
Script de exemplo para testar a detecção de nudez com image.png
"""

import os
import sys
from pathlib import Path


project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from detector_nudez import DetectorNudez, imprimir_resultado

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = YELLOW = GREEN = CYAN = BLUE = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = RESET_ALL = ''

def main():
    """Exemplo de uso do detector com image.png"""


    caminho_imagem = "image.png"


    if not os.path.exists(caminho_imagem):
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Imagem '{caminho_imagem}' nao encontrada!")
        print(f"{Fore.YELLOW}Certifique-se de que a imagem esta na mesma pasta do script.{Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}  EXEMPLO DE USO - DETECTOR DE NUDEZ{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


    detector = DetectorNudez(threshold=0.2, debug=True)


    print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} {caminho_imagem}")
    resultado = detector.detectar_imagem(caminho_imagem)


    resultado_blur = None
    if resultado.get('tem_nudez') and not resultado.get('erro'):
        print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} Aplicando blur nas areas detectadas...")
        resultado_blur = detector.aplicar_blur(
            caminho_imagem,
            resultado,
            intensidade_blur=85,
            margem_percentual=45
        )


    imprimir_resultado(resultado, resultado_blur)

    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Dica:{Style.RESET_ALL} Use o script principal para mais opcoes:")
    print(f"   {Fore.WHITE}python3 detector_nudez.py {caminho_imagem}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}python3 detector_nudez.py --blur {caminho_imagem}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()

