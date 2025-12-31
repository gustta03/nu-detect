
"""
Script de exemplo para processar vídeo e retornar vídeo MP4 editado com blur
"""

import os
import sys
from pathlib import Path


project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from detector_nudez_v2 import DetectorNudez

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = YELLOW = GREEN = CYAN = BLUE = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = RESET_ALL = ''

def main():
    """Exemplo de uso do detector com vídeo completo (retorna MP4 editado)"""

    if len(sys.argv) < 2:
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Forneça o caminho do vídeo")
        print(f"{Fore.YELLOW}Uso: python3 exemplo_video_com_blur.py <caminho_video> [caminho_saida]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Exemplo: python3 exemplo_video_com_blur.py video.mp4 video_editado.mp4{Style.RESET_ALL}")
        sys.exit(1)

    caminho_video = sys.argv[1]
    caminho_saida = sys.argv[2] if len(sys.argv) > 2 else None


    if not os.path.exists(caminho_video):
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Vídeo '{caminho_video}' não encontrado!")
        sys.exit(1)

    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}  PROCESSAMENTO DE VÍDEO COM BLUR - RETORNA MP4 EDITADO{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


    detector = DetectorNudez(threshold=0.30, debug=False)


    print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} {caminho_video}")
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Processando TODOS os frames e aplicando blur onde necessário...")

    resultado = detector.processar_video_com_blur(
        caminho_video,
        caminho_saida=caminho_saida,
        intensidade_blur=75,
        margem_percentual=40,
        intervalo_segundos=1.0
    )

    if resultado.get('erro'):
        print(f"\n{Fore.RED}[ERRO]{Style.RESET_ALL} {resultado.get('mensagem', 'Erro desconhecido')}")
        sys.exit(1)


    print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}[SUCESSO]{Style.RESET_ALL} Vídeo processado com sucesso!")
    print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Vídeo editado:{Style.RESET_ALL} {resultado.get('video_editado')}")
    print(f"{Fore.CYAN}Total de frames processados (amostrados):{Style.RESET_ALL} {resultado.get('total_frames_processados')}")
    print(f"{Fore.CYAN}Total de frames no vídeo:{Style.RESET_ALL} {resultado.get('total_frames_video', resultado.get('total_frames_processados'))}")
    print(f"{Fore.CYAN}Frames com blur aplicado:{Style.RESET_ALL} {resultado.get('total_frames_com_blur')}")
    print(f"{Fore.CYAN}Intervalo usado:{Style.RESET_ALL} {resultado.get('intervalo_usado', 1.0)} segundo(s)")
    print(f"{Fore.CYAN}Duração total:{Style.RESET_ALL} {detector._formatar_tempo(resultado.get('duracao_total', 0))}")
    print(f"{Fore.CYAN}FPS:{Style.RESET_ALL} {resultado.get('fps', 0):.2f}")
    print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

