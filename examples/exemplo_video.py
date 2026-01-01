
"""
Script de exemplo para processar vídeo e detectar nudez frame a frame
"""

import os
import sys
from pathlib import Path


project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from detector_nudez import DetectorNudez, imprimir_resultado_video

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = YELLOW = GREEN = CYAN = BLUE = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = RESET_ALL = ''

def main():
    """Exemplo de uso do detector com vídeo"""

    if len(sys.argv) < 2:
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Forneca o caminho do video")
        print(f"{Fore.YELLOW}Uso: python3 exemplo_video.py <caminho_video> [intervalo_segundos]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Exemplo: python3 exemplo_video.py video.mp4 1.0{Style.RESET_ALL}")
        sys.exit(1)

    caminho_video = sys.argv[1]
    intervalo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0


    if not os.path.exists(caminho_video):
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Video '{caminho_video}' nao encontrado!")
        sys.exit(1)

    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}  PROCESSAMENTO DE VIDEO - DETECTOR DE NUDEZ{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


    detector = DetectorNudez(threshold=0.2, debug=False)


    print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} {caminho_video}")
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Intervalo entre frames: {intervalo} segundo(s)")
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Blur sera aplicado automaticamente nos frames com NSFW")

    resultado_video = detector.processar_video(
        caminho_video,
        intervalo,
        aplicar_blur_frames=True
    )


    imprimir_resultado_video(resultado_video)

    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Dica:{Style.RESET_ALL} Use o script principal para mais opcoes:")
    print(f"   {Fore.WHITE}python -m src.detector_nudez --video video.mp4{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}python -m src.detector_nudez --video --intervalo 2.0 video.mp4{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()

