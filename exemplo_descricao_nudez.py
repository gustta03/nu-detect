#!/usr/bin/env python3
"""
Exemplo de uso da função obter_descricao_nudez
Retorna apenas informações textuais sobre a detecção, sem processar frames
"""

import sys
import os
from detector_nudez_v2 import DetectorNudez

def main():
    if len(sys.argv) < 2:
        print("Uso: python exemplo_descricao_nudez.py <caminho_imagem>")
        sys.exit(1)
    
    caminho_imagem = sys.argv[1]
    
    if not os.path.exists(caminho_imagem):
        print(f"Erro: Arquivo não encontrado: {caminho_imagem}")
        sys.exit(1)
    
    # Inicializa detector
    detector = DetectorNudez(threshold=0.30, debug=False)
    
    # Obtém descrição textual
    resultado = detector.obter_descricao_nudez(caminho_imagem)
    
    # Exibe resultado
    print("\n" + "="*70)
    print("RESULTADO DA ANÁLISE")
    print("="*70)
    
    if resultado.get('erro'):
        print(f"ERRO: {resultado.get('mensagem', 'Erro desconhecido')}")
        sys.exit(1)
    
    print(f"\nTem nudez: {'SIM' if resultado['tem_nudez'] else 'NÃO'}")
    print(f"Tipo de nudez: {resultado['tipo_nudez']}")
    print(f"Confiança: {resultado['confianca']:.2f}%")
    print(f"Humanos detectados: {resultado.get('humanos_detectados', 0)}")
    print(f"\nDescrição:")
    print(f"  {resultado['descricao']}")
    
    if resultado.get('partes_detectadas'):
        print(f"\nPartes detectadas ({resultado.get('total_partes', 0)}):")
        for parte in resultado['partes_detectadas']:
            print(f"  - {parte}")
    
    print("\n" + "="*70)
    
    # Retorna como JSON (opcional)
    import json
    print("\nResultado em JSON:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()

