#!/usr/bin/env python3
"""
Script de exemplo para testar a detecção de nudez com image.png
"""

import os
import sys
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
    
    # Caminho da imagem
    caminho_imagem = "image.png"
    
    # Verifica se a imagem existe
    if not os.path.exists(caminho_imagem):
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Imagem '{caminho_imagem}' nao encontrada!")
        print(f"{Fore.YELLOW}Certifique-se de que a imagem esta na mesma pasta do script.{Style.RESET_ALL}")
        sys.exit(1)
    
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}  EXEMPLO DE USO - DETECTOR DE NUDEZ{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    # Inicializa o detector com threshold mais baixo (mais sensível) e modo debug
    detector = DetectorNudez(threshold=0.2, debug=True)
    
    # Detecta nudez na imagem
    print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} {caminho_imagem}")
    resultado = detector.detectar_imagem(caminho_imagem)
    
    # Aplica blur se detectar nudez (com margem de 30% para melhor cobertura)
    resultado_blur = None
    if resultado.get('tem_nudez') and not resultado.get('erro'):
        print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} Aplicando blur nas areas detectadas...")
        resultado_blur = detector.aplicar_blur(
            caminho_imagem, 
            resultado, 
            intensidade_blur=85,  # Blur mais intenso para garantir cobertura total
            margem_percentual=45  # Margem maior para garantir que nada vaze
        )
    
    # Mostra resultado usando a função formatada
    imprimir_resultado(resultado, resultado_blur)
    
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Dica:{Style.RESET_ALL} Use o script principal para mais opcoes:")
    print(f"   {Fore.WHITE}python3 detector_nudez.py {caminho_imagem}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}python3 detector_nudez.py --blur {caminho_imagem}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()

