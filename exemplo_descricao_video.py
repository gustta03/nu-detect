#!/usr/bin/env python3
"""
Exemplo de uso da função obter_descricao_nudez_video
Retorna apenas informações textuais sobre a detecção no vídeo, sem processar frames
"""

import sys
import os
import json
from detector_nudez_v2 import DetectorNudez

def main():
    if len(sys.argv) < 2:
        print("Uso: python exemplo_descricao_video.py <caminho_video> [intervalo_segundos]")
        print("  intervalo_segundos: Intervalo entre frames (padrão: 1.0)")
        sys.exit(1)
    
    caminho_video = sys.argv[1]
    intervalo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    
    if not os.path.exists(caminho_video):
        print(f"Erro: Arquivo não encontrado: {caminho_video}")
        sys.exit(1)
    
    # Inicializa detector
    print("Inicializando detector...")
    detector = DetectorNudez(threshold=0.30, debug=False)
    
    # Obtém descrição textual do vídeo
    print(f"\nProcessando vídeo: {caminho_video}")
    print(f"Intervalo entre frames: {intervalo} segundo(s)")
    print("Processando...\n")
    
    resultado = detector.obter_descricao_nudez_video(caminho_video, intervalo_segundos=intervalo)
    
    # Exibe resultado
    print("\n" + "="*70)
    print("RESULTADO DA ANÁLISE DO VÍDEO")
    print("="*70)
    
    if resultado.get('erro'):
        print(f"ERRO: {resultado.get('mensagem', 'Erro desconhecido')}")
        sys.exit(1)
    
    print(f"\nVídeo: {os.path.basename(caminho_video)}")
    print(f"Duração: {resultado['duracao_formatada']} ({resultado['duracao_total']:.2f}s)")
    print(f"Frames processados: {resultado['total_frames_processados']}")
    
    print(f"\nTem nudez: {'SIM' if resultado['tem_nudez'] else 'NÃO'}")
    print(f"Tipo de nudez: {resultado['tipo_nudez']}")
    print(f"\nDescrição geral:")
    print(f"  {resultado['descricao_geral']}")
    
    if resultado.get('resumo'):
        resumo = resultado['resumo']
        print(f"\nEstatísticas:")
        if 'total_frames_nsfw' in resumo:
            print(f"  Frames NSFW: {resumo['total_frames_nsfw']}")
            print(f"  Frames SUGGESTIVE: {resumo['total_frames_suggestive']}")
            print(f"  Frames SAFE: {resumo['total_frames_safe']}")
    
    if resultado.get('timestamps'):
        print(f"\nTimestamps com detecção ({len(resultado['timestamps'])}):")
        print("-" * 70)
        
        for i, ts_info in enumerate(resultado['timestamps'][:20], 1):  # Mostra primeiros 20
            print(f"\n{i}. Timestamp: {ts_info['tempo_formatado']} ({ts_info['timestamp']:.2f}s)")
            print(f"   Tipo: {ts_info['tipo_nudez']}")
            print(f"   Descrição: {ts_info['descricao']}")
        
        if len(resultado['timestamps']) > 20:
            print(f"\n... e mais {len(resultado['timestamps']) - 20} timestamp(s)")
    else:
        print("\nNenhum timestamp com detecção encontrado.")
    
    print("\n" + "="*70)
    
    # Opção para salvar JSON
    salvar_json = input("\nDeseja salvar resultado em JSON? (s/n): ").lower() == 's'
    if salvar_json:
        arquivo_json = f"resultado_{os.path.splitext(os.path.basename(caminho_video))[0]}.json"
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        print(f"\nResultado salvo em: {arquivo_json}")

if __name__ == '__main__':
    main()

