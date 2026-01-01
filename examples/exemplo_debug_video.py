#!/usr/bin/env python3
"""
Script de DEBUG para análise detalhada de vídeo
Mostra informações de cada frame processado
"""

import sys
import os
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from detector_nudez_v2 import DetectorNudez

def main():
    if len(sys.argv) < 2:
        print("Uso: python exemplo_debug_video.py <caminho_video> [intervalo_segundos]")
        print("  intervalo_segundos: Intervalo entre frames (padrão: 0.5)")
        sys.exit(1)

    caminho_video = sys.argv[1]
    intervalo = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

    if not os.path.exists(caminho_video):
        print(f"Erro: Arquivo não encontrado: {caminho_video}")
        sys.exit(1)

    print("Inicializando detector...")
    detector = DetectorNudez(threshold=0.30, debug=False)

    print(f"\n🔍 DEBUG: Processando vídeo: {caminho_video}")
    print(f"Intervalo entre frames: {intervalo} segundo(s)")
    print("="*80)
    print()

    resultado = detector.obter_descricao_nudez_video_debug(caminho_video, intervalo_segundos=intervalo)

    if resultado.get('erro'):
        print(f"❌ ERRO: {resultado.get('mensagem', 'Erro desconhecido')}")
        sys.exit(1)

    print("\n" + "="*80)
    print("📊 RESUMO GERAL")
    print("="*80)
    print(f"Vídeo: {os.path.basename(caminho_video)}")
    print(f"Duração: {resultado['duracao_formatada']} ({resultado['duracao_total']:.2f}s)")
    print(f"Frames processados: {resultado['total_frames_processados']}")
    print(f"Tem nudez: {'SIM' if resultado['tem_nudez'] else 'NÃO'}")
    print(f"Tipo de nudez: {resultado['tipo_nudez']}")
    print(f"Descrição geral: {resultado['descricao_geral']}")

    if resultado.get('resumo'):
        resumo = resultado['resumo']
        print(f"\nEstatísticas:")
        print(f"  Frames NSFW: {resumo.get('total_frames_nsfw', 0)}")
        print(f"  Frames SUGGESTIVE: {resumo.get('total_frames_suggestive', 0)}")
        print(f"  Frames SAFE: {resumo.get('total_frames_safe', 0)}")

    print("\n" + "="*80)
    print("📋 DETALHES POR FRAME (DEBUG)")
    print("="*80)

    debug_info = resultado.get('debug_info', [])
    for frame_debug in debug_info:
        timestamp = frame_debug['tempo_formatado']
        severity_detected = frame_debug.get('severity_detected', 'UNKNOWN')
        severity_final = frame_debug.get('severity_final', 'UNKNOWN')
        confirmed = frame_debug.get('confirmed_nudity', False)
        included = frame_debug.get('included', False)
        included_reason = frame_debug.get('included_reason', '')
        
        # Emoji baseado na severidade
        if severity_detected == 'NSFW':
            emoji = "🔴"
        elif severity_detected == 'SUGGESTIVE':
            emoji = "🟠"
        else:
            emoji = "🟢"
        
        status = "✅ INCLUÍDO" if included else "❌ EXCLUÍDO"
        
        print(f"\n{emoji} {timestamp} ({frame_debug['timestamp']:.1f}s) - {status}")
        print(f"   Severidade Detectada: {severity_detected}")
        print(f"   Severidade Final (pós-agregação): {severity_final}")
        print(f"   Confirmado temporalmente: {confirmed}")
        print(f"   Motivo: {included_reason}")
        
        if not detector.use_legacy:
            humans = frame_debug.get('humans_detected', 0)
            parts = frame_debug.get('parts_detected', [])
            confidence = frame_debug.get('confidence', 0)
            consecutive = frame_debug.get('temporal_consecutive', 0)
            score = frame_debug.get('temporal_score', 0)
            
            print(f"   Humanos detectados: {humans}")
            print(f"   Confiança: {confidence:.2f}%")
            print(f"   Frames consecutivos NSFW: {consecutive}")
            print(f"   Score acumulado: {score:.2f}")
            
            if parts:
                print(f"   Partes detectadas ({len(parts)}):")
                for part in parts:
                    print(f"     - {part['class']}: {part['confidence']:.1f}%")

    print("\n" + "="*80)
    print("📝 TIMESTAMPS INCLUÍDOS NO RESULTADO FINAL")
    print("="*80)
    
    if resultado.get('timestamps'):
        for i, ts_info in enumerate(resultado['timestamps'], 1):
            print(f"\n{i}. {ts_info['tempo_formatado']} ({ts_info['timestamp']:.1f}s) [{ts_info['tipo_nudez']}]")
            print(f"   {ts_info['descricao']}")
    else:
        print("\nNenhum timestamp com detecção encontrado.")

    print("\n" + "="*80)

    # Salvar JSON completo
    arquivo_json = f"debug_{os.path.splitext(os.path.basename(caminho_video))[0]}.json"
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Resultado completo salvo em: {arquivo_json}")

if __name__ == '__main__':
    main()


