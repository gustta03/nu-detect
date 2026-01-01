#!/usr/bin/env python3
"""
Script de debug específico para verificar detecção de genitálias masculinas.
Mostra TODAS as detecções brutas do NudeNet, antes dos filtros.
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from nudenet import NudeDetector
    import cv2
    import json
    from src.detector_nudez_v2 import DetectorNudez
except ImportError as e:
    print(f"Erro ao importar: {e}")
    sys.exit(1)

def debug_male_genitalia(video_path: str, output_json: str = "debug_male_genitalia.json"):
    """
    Debug específico para genitálias masculinas.
    Mostra todas as detecções brutas do NudeNet.
    """
    print("=" * 80)
    print("🔍 DEBUG: Detecção de Genitálias Masculinas")
    print("=" * 80)
    print(f"Vídeo: {video_path}")
    print()
    
    # Inicializa o detector
    detector = DetectorNudez(threshold=0.20)
    
    # Abre o vídeo
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Erro ao abrir vídeo: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"FPS: {fps:.2f}")
    print(f"Total de frames: {total_frames}")
    print(f"Duração: {duration:.2f}s")
    print()
    
    # NudeNet direto (sem filtros)
    nudenet_detector = NudeDetector()
    
    frame_number = 0
    debug_info = []
    detections_found = {
        'MALE_GENITALIA': [],
        'FEMALE_GENITALIA': [],
        'GENITALIA': [],
        'BREAST': [],
        'all_classes': set()
    }
    
    print("📹 Processando frames...")
    print("-" * 80)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        timestamp = frame_number / fps if fps > 0 else 0
        
        # Salva frame temporário
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, frame)
        
        try:
            # Detecção BRUTA do NudeNet (sem filtros)
            raw_detections = nudenet_detector.detect(tmp_path)
            
            # Agrupa detecções por tipo
            frame_detections = {
                'timestamp': timestamp,
                'frame': frame_number,
                'raw_detections': [],
                'has_male_genitalia': False,
                'has_female_genitalia': False,
                'has_genitalia': False,
                'has_breast': False
            }
            
            for det in raw_detections:
                class_name = det.get('class', '')
                score = det.get('score', 0.0)
                bbox = det.get('box', [])
                
                det_info = {
                    'class': class_name,
                    'score': score,
                    'bbox': bbox
                }
                
                frame_detections['raw_detections'].append(det_info)
                detections_found['all_classes'].add(class_name)
                
                # Verifica tipos específicos
                class_upper = class_name.upper()
                
                if 'MALE' in class_upper and 'GENITALIA' in class_upper:
                    frame_detections['has_male_genitalia'] = True
                    detections_found['MALE_GENITALIA'].append({
                        'frame': frame_number,
                        'timestamp': timestamp,
                        'class': class_name,
                        'score': score
                    })
                    print(f"🎯 Frame {frame_number:5d} ({timestamp:6.2f}s): MALE_GENITALIA detectado!")
                    print(f"   Classe: {class_name}, Score: {score:.4f}")
                
                if 'FEMALE' in class_upper and 'GENITALIA' in class_upper:
                    frame_detections['has_female_genitalia'] = True
                    detections_found['FEMALE_GENITALIA'].append({
                        'frame': frame_number,
                        'timestamp': timestamp,
                        'class': class_name,
                        'score': score
                    })
                
                if 'GENITALIA' in class_upper or 'GENITAL' in class_upper:
                    frame_detections['has_genitalia'] = True
                    detections_found['GENITALIA'].append({
                        'frame': frame_number,
                        'timestamp': timestamp,
                        'class': class_name,
                        'score': score
                    })
                
                if 'BREAST' in class_upper:
                    frame_detections['has_breast'] = True
                    detections_found['BREAST'].append({
                        'frame': frame_number,
                        'timestamp': timestamp,
                        'class': class_name,
                        'score': score
                    })
            
            # Só adiciona ao debug se houver detecções
            if frame_detections['raw_detections']:
                debug_info.append(frame_detections)
            
            # Log a cada 30 frames se houver detecções interessantes
            if frame_number % 30 == 0 or frame_detections['has_male_genitalia'] or frame_detections['has_female_genitalia']:
                if frame_detections['raw_detections']:
                    print(f"Frame {frame_number:5d} ({timestamp:6.2f}s): {len(frame_detections['raw_detections'])} detecções")
                    for det in frame_detections['raw_detections'][:3]:  # Mostra até 3
                        print(f"  - {det['class']:30s} score: {det['score']:.4f}")
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        frame_number += 1
        
        # Processa apenas até 10 segundos para debug rápido (comente para processar tudo)
        if frame_number >= int(fps * 60):  # Primeiros 60 segundos
            break
    
    cap.release()
    
    print()
    print("=" * 80)
    print("📊 RESUMO DAS DETECÇÕES BRUTAS (NudeNet)")
    print("=" * 80)
    
    print(f"\n🔍 Todas as classes detectadas pelo NudeNet:")
    for cls in sorted(detections_found['all_classes']):
        print(f"  - {cls}")
    
    print(f"\n👨 Genitálias MASCULINAS detectadas: {len(detections_found['MALE_GENITALIA'])}")
    if detections_found['MALE_GENITALIA']:
        for det in detections_found['MALE_GENITALIA'][:10]:  # Primeiras 10
            print(f"  Frame {det['frame']:5d} ({det['timestamp']:6.2f}s): {det['class']} score={det['score']:.4f}")
        if len(detections_found['MALE_GENITALIA']) > 10:
            print(f"  ... e mais {len(detections_found['MALE_GENITALIA']) - 10}")
    else:
        print("  ❌ NENHUMA genitália masculina detectada pelo NudeNet")
    
    print(f"\n👩 Genitálias FEMININAS detectadas: {len(detections_found['FEMALE_GENITALIA'])}")
    if detections_found['FEMALE_GENITALIA']:
        for det in detections_found['FEMALE_GENITALIA'][:10]:
            print(f"  Frame {det['frame']:5d} ({det['timestamp']:6.2f}s): {det['class']} score={det['score']:.4f}")
    
    print(f"\n🔞 Genitálias (qualquer gênero): {len(detections_found['GENITALIA'])}")
    
    print(f"\n👙 Seios detectados: {len(detections_found['BREAST'])}")
    if detections_found['BREAST']:
        for det in detections_found['BREAST'][:5]:
            print(f"  Frame {det['frame']:5d} ({det['timestamp']:6.2f}s): {det['class']} score={det['score']:.4f}")
    
    # Salva JSON completo
    output_data = {
        'video_path': video_path,
        'total_frames_processed': frame_number,
        'duration': duration,
        'summary': {
            'male_genitalia_count': len(detections_found['MALE_GENITALIA']),
            'female_genitalia_count': len(detections_found['FEMALE_GENITALIA']),
            'all_genitalia_count': len(detections_found['GENITALIA']),
            'breast_count': len(detections_found['BREAST']),
            'all_classes_detected': sorted(list(detections_found['all_classes']))
        },
        'male_genitalia_detections': detections_found['MALE_GENITALIA'],
        'female_genitalia_detections': detections_found['FEMALE_GENITALIA'],
        'all_genitalia_detections': detections_found['GENITALIA'],
        'breast_detections': detections_found['BREAST'],
        'frame_details': debug_info
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detalhes completos salvos em: {output_json}")
    print("=" * 80)
    
    # Diagnóstico
    print("\n🔬 DIAGNÓSTICO:")
    if len(detections_found['MALE_GENITALIA']) == 0:
        print("❌ PROBLEMA: NudeNet NÃO detectou genitálias masculinas")
        print("   Possíveis causas:")
        print("   1. O modelo NudeNet pode ter viés (treinado principalmente com nudez feminina)")
        print("   2. As genitálias masculinas podem estar com baixa visibilidade/qualidade")
        print("   3. O modelo pode usar classes diferentes (verificar 'all_classes_detected')")
    else:
        print(f"✅ NudeNet detectou {len(detections_found['MALE_GENITALIA'])} genitálias masculinas")
        avg_score = sum(d['score'] for d in detections_found['MALE_GENITALIA']) / len(detections_found['MALE_GENITALIA'])
        print(f"   Score médio: {avg_score:.4f}")
        min_score = min(d['score'] for d in detections_found['MALE_GENITALIA'])
        print(f"   Score mínimo: {min_score:.4f}")
        threshold = 0.20 * 0.3  # base_threshold * 0.3
        print(f"   Threshold atual: {threshold:.4f}")
        if min_score < threshold:
            print(f"   ⚠️  ALGUMAS detecções estão abaixo do threshold!")
    
    print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python exemplo_debug_male_genitalia.py <video_path> [output_json]")
        print("\nExemplo:")
        print("  python exemplo_debug_male_genitalia.py data/videos/teste.mp4 debug_male.json")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else "debug_male_genitalia.json"
    
    if not Path(video_path).exists():
        print(f"❌ Vídeo não encontrado: {video_path}")
        sys.exit(1)
    
    debug_male_genitalia(video_path, output_json)


