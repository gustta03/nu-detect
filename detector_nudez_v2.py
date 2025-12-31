#!/usr/bin/env python3
"""
Aplicação para detecção de nudez em imagens e vídeos - Versão 2.0

Arquitetura multiestágio:
1. Detecção de humanos (YOLOv8)
2. Análise de nudez (NudeNet apenas em bounding boxes)
3. Classificação hierárquica (SAFE, SUGGESTIVE, NSFW)
4. Agregação temporal (vídeo)
5. Observabilidade (logs estruturados)
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = YELLOW = GREEN = CYAN = BLUE = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = RESET_ALL = ''
    class Back:
        RED = YELLOW = GREEN = RESET = ''

try:
    from nudity_pipeline import NudityDetectionPipeline
    from severity_classifier import SeverityLevel
except ImportError as e:
    print(f"{Fore.RED}Erro: Módulos do pipeline não encontrados.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Erro: {e}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Certifique-se de que todos os módulos estão no mesmo diretório.{Style.RESET_ALL}")
    sys.exit(1)


class DetectorNudez:
    """
    Classe para detectar conteúdo NSFW em imagens e vídeos.
    
    Usa pipeline multiestágio robusto que:
    - Detecta humanos antes de analisar nudez
    - Analisa nudez apenas em bounding boxes de pessoas
    - Classifica severidade hierarquicamente
    - Agrega temporalmente para vídeo
    """
    
    def __init__(self, threshold=0.30, debug=False, use_legacy=False):
        """
        Inicializa o detector
        
        Args:
            threshold (float): Threshold de confiança base (0.0 a 1.0, padrão: 0.30)
            debug (bool): Se True, mostra todas as detecções e logs detalhados
            use_legacy (bool): Se True, usa implementação antiga (não recomendado)
        """
        self.threshold = threshold
        self.debug = debug
        self.use_legacy = use_legacy
        
        if use_legacy:
            print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Usando implementação legada (não recomendado)")
            self._init_legacy()
        else:
            print(f"{Fore.CYAN}Inicializando pipeline multiestágio...{Style.RESET_ALL}")
            try:
                self.pipeline = NudityDetectionPipeline(
                    nudity_base_threshold=threshold,
                    debug=debug
                )
                print(f"{Fore.GREEN}{Style.BRIGHT}Pipeline inicializado com sucesso!{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Erro ao inicializar pipeline: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Tentando usar implementação legada...{Style.RESET_ALL}")
                self.use_legacy = True
                self._init_legacy()
    
    def _init_legacy(self):
        """Inicializa implementação legada (fallback)."""
        try:
            from nudenet import NudeDetector
            self.detector = NudeDetector()
        except ImportError:
            print(f"{Fore.RED}Erro: Biblioteca nudenet não encontrada.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Execute: pip install -r requirements.txt{Style.RESET_ALL}")
            sys.exit(1)
    
    def detectar_imagem(self, caminho_imagem):
        """
        Detecta nudez em uma imagem
        
        Args:
            caminho_imagem (str): Caminho para a imagem
            
        Returns:
            dict: Resultado da detecção (formato compatível com versão antiga)
        """
        if not os.path.exists(caminho_imagem):
            return {
                'erro': True,
                'mensagem': f'Arquivo não encontrado: {caminho_imagem}'
            }
        
        if self.use_legacy:
            return self._detectar_imagem_legacy(caminho_imagem)
        
        try:
            # Usa novo pipeline
            resultado = self.pipeline.process_image(caminho_imagem)
            
            # Converte para formato compatível
            tem_nudez = resultado['nudity_detected']
            severity = resultado['severity']
            
            # Converte partes detectadas para formato antigo
            deteccoes = []
            for part in resultado.get('parts_detected', []):
                deteccoes.append({
                    'classe': part.get('class_name', ''),
                    'confianca': round(part.get('score', 0.0) * 100, 2),
                    'bbox': part.get('absolute_bbox', [])
                })
            
            return {
                'erro': False,
                'tem_nudez': tem_nudez and severity != SeverityLevel.SAFE.value,
                'severity': severity,
                'confianca': round(resultado['confidence'] * 100, 2),
                'deteccoes': deteccoes,
                'total_deteccoes': len(deteccoes),
                'caminho': caminho_imagem,
                'threshold_usado': self.threshold,
                'humans_detected': resultado.get('humans_detected', 0),
                'pipeline_result': resultado  # Resultado completo do pipeline
            }
            
        except Exception as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao processar imagem: {str(e)}'
            }
    
    def obter_descricao_nudez(self, caminho_imagem):
        """
        Analisa imagem e retorna apenas informações textuais sobre a detecção de nudez.
        Não processa frames, apenas retorna descrição.
        
        Args:
            caminho_imagem (str): Caminho para a imagem
            
        Returns:
            dict: Informações textuais sobre a detecção:
                {
                    'tem_nudez': bool,
                    'tipo_nudez': str,  # 'SAFE', 'SUGGESTIVE', 'NSFW'
                    'descricao': str,   # Descrição detalhada da nudez
                    'confianca': float, # Confiança da detecção (0-100)
                    'partes_detectadas': list,  # Lista de partes detectadas
                    'erro': bool,
                    'mensagem': str     # Mensagem de erro se houver
                }
        """
        if not os.path.exists(caminho_imagem):
            return {
                'erro': True,
                'mensagem': f'Arquivo não encontrado: {caminho_imagem}',
                'tem_nudez': False,
                'tipo_nudez': 'SAFE',
                'descricao': 'Arquivo não encontrado'
            }
        
        try:
            # Usa detecção normal
            resultado = self.detectar_imagem(caminho_imagem)
            
            if resultado.get('erro'):
                return {
                    'erro': True,
                    'mensagem': resultado.get('mensagem', 'Erro desconhecido'),
                    'tem_nudez': False,
                    'tipo_nudez': 'SAFE',
                    'descricao': 'Erro ao processar imagem'
                }
            
            # Extrai informações
            tem_nudez = resultado.get('tem_nudez', False)
            severity = resultado.get('severity', 'SAFE')
            confianca = resultado.get('confianca', 0.0)
            pipeline_result = resultado.get('pipeline_result', {})
            severity_result = pipeline_result.get('severity_result', {})
            
            # Obtém descrição do severity_result
            descricao_base = severity_result.get('reason', '')
            
            # Lista partes detectadas
            partes_detectadas = []
            deteccoes = resultado.get('deteccoes', [])
            
            # Agrupa partes por tipo
            partes_por_tipo = {}
            for det in deteccoes:
                classe = det.get('classe', '')
                conf = det.get('confianca', 0.0)
                
                # Classifica tipo
                tipo = 'outro'
                if 'BREAST' in classe.upper():
                    tipo = 'seios'
                elif 'NIPPLE' in classe.upper():
                    tipo = 'mamilos'
                elif 'GENITALIA' in classe.upper() or 'GENITAL' in classe.upper():
                    tipo = 'genitália'
                elif 'ANUS' in classe.upper():
                    tipo = 'ânus'
                elif 'BUTTOCK' in classe.upper():
                    tipo = 'nádegas'
                
                if tipo not in partes_por_tipo:
                    partes_por_tipo[tipo] = []
                partes_por_tipo[tipo].append({
                    'classe': classe,
                    'confianca': conf
                })
                partes_detectadas.append(classe)
            
            # Gera descrição detalhada
            if severity == 'SAFE':
                descricao = 'Nenhum conteúdo sensível detectado na imagem.'
            elif severity == 'SUGGESTIVE':
                desc_parts = []
                if 'seios' in partes_por_tipo:
                    desc_parts.append('seios expostos sem mamilos visíveis')
                if 'outro' in partes_por_tipo:
                    outras = [p['classe'] for p in partes_por_tipo['outro']]
                    if outras:
                        desc_parts.append(f"outras partes: {', '.join(outras[:3])}")
                
                if desc_parts:
                    descricao = f'Conteúdo sugestivo detectado: {", ".join(desc_parts)}. {descricao_base}'
                else:
                    descricao = f'Conteúdo sugestivo detectado. {descricao_base}'
            elif severity == 'NSFW':
                desc_parts = []
                if 'genitália' in partes_por_tipo:
                    desc_parts.append('genitália exposta')
                if 'ânus' in partes_por_tipo:
                    desc_parts.append('ânus exposto')
                if 'mamilos' in partes_por_tipo:
                    desc_parts.append('mamilos expostos')
                if 'seios' in partes_por_tipo and 'mamilos' not in partes_por_tipo:
                    desc_parts.append('seios completamente expostos')
                if 'nádegas' in partes_por_tipo:
                    desc_parts.append('nádegas expostas')
                
                if desc_parts:
                    descricao = f'Conteúdo explícito (NSFW) detectado: {", ".join(desc_parts)}. {descricao_base}'
                else:
                    descricao = f'Conteúdo explícito (NSFW) detectado. {descricao_base}'
            else:
                descricao = descricao_base if descricao_base else 'Conteúdo desconhecido detectado.'
            
            return {
                'erro': False,
                'tem_nudez': tem_nudez,
                'tipo_nudez': severity,
                'descricao': descricao,
                'confianca': confianca,
                'partes_detectadas': list(set(partes_detectadas)),  # Remove duplicatas
                'total_partes': len(set(partes_detectadas)),
                'humanos_detectados': resultado.get('humans_detected', 0)
            }
            
        except Exception as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao analisar imagem: {str(e)}',
                'tem_nudez': False,
                'tipo_nudez': 'SAFE',
                'descricao': f'Erro ao processar: {str(e)}'
            }
    
    def _detectar_imagem_legacy(self, caminho_imagem):
        """Implementação legada (fallback)."""
        # Implementação simplificada da versão antiga
        try:
            imagem = Image.open(caminho_imagem)
            imagem.verify()
            
            resultado = self.detector.detect(caminho_imagem)
            
            tem_nudez = False
            confianca_total = 0.0
            deteccoes = []
            
            for deteccao in resultado:
                classe = deteccao.get('class', '')
                score = deteccao.get('score', 0)
                
                # Filtros básicos
                is_nsfw = any(kw in classe.upper() for kw in 
                            ['GENITALIA_EXPOSED', 'ANUS_EXPOSED', 'NIPPLE_EXPOSED', 
                             'BUTTOCK_EXPOSED', 'BREAST_EXPOSED'])
                
                if is_nsfw and score >= self.threshold:
                    bbox = deteccao.get('box') or deteccao.get('bbox')
                    deteccoes.append({
                        'classe': classe,
                        'confianca': round(score * 100, 2),
                        'bbox': bbox
                    })
                    tem_nudez = True
                    confianca_total = max(confianca_total, score)
            
            return {
                'erro': False,
                'tem_nudez': tem_nudez,
                'confianca': round(confianca_total * 100, 2),
                'deteccoes': deteccoes,
                'total_deteccoes': len(deteccoes),
                'caminho': caminho_imagem,
                'threshold_usado': self.threshold
            }
            
        except Exception as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao processar imagem: {str(e)}'
            }
    
    def detectar_pasta(self, caminho_pasta):
        """
        Detecta nudez em todas as imagens de uma pasta
        
        Args:
            caminho_pasta (str): Caminho para a pasta com imagens
            
        Returns:
            list: Lista de resultados para cada imagem
        """
        if not os.path.isdir(caminho_pasta):
            return [{
                'erro': True,
                'mensagem': f'Pasta não encontrada: {caminho_pasta}'
            }]
        
        extensoes_validas = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        resultados = []
        
        for arquivo in os.listdir(caminho_pasta):
            caminho_completo = os.path.join(caminho_pasta, arquivo)
            if os.path.isfile(caminho_completo):
                extensao = Path(arquivo).suffix.lower()
                if extensao in extensoes_validas:
                    print(f"\nProcessando: {arquivo}")
                    resultado = self.detectar_imagem(caminho_completo)
                    resultados.append(resultado)
        
        return resultados
    
    def processar_video(self, caminho_video, intervalo_segundos=1.0, 
                       pasta_frames=None, aplicar_blur_frames=True, 
                       pasta_saida_frames=None):
        """
        Extrai frames de um vídeo e detecta nudez em cada frame
        
        Args:
            caminho_video (str): Caminho para o vídeo
            intervalo_segundos (float): Intervalo entre frames extraídos
            pasta_frames (str): Pasta temporária para frames
            aplicar_blur_frames (bool): Se True, aplica blur nos frames com NSFW
            pasta_saida_frames (str): Pasta para salvar frames editados
            
        Returns:
            dict: Resultado com timestamps onde há nudez detectada
        """
        if not os.path.exists(caminho_video):
            return {
                'erro': True,
                'mensagem': f'Video nao encontrado: {caminho_video}'
            }
        
        # Verifica ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'erro': True,
                'mensagem': 'FFmpeg nao encontrado. Instale com: sudo apt install ffmpeg'
            }
        
        # Cria pasta temporária
        pasta_temp = None
        if pasta_frames is None:
            pasta_temp = tempfile.mkdtemp(prefix='nudez_frames_')
            pasta_frames = pasta_temp
        else:
            os.makedirs(pasta_frames, exist_ok=True)
        
        try:
            # Obtém duração do vídeo
            cmd_duracao = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', caminho_video
            ]
            resultado_duracao = subprocess.run(cmd_duracao, 
                                             capture_output=True, 
                                             text=True, 
                                             check=True)
            duracao_total = float(resultado_duracao.stdout.strip())
            
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Duracao do video: {self._formatar_tempo(duracao_total)}")
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Extraindo frames a cada {intervalo_segundos} segundo(s)...")
            
            # Extrai frames
            fps_extrair = 1.0 / intervalo_segundos
            padrao_frame = os.path.join(pasta_frames, 'frame_%06d.jpg')
            
            cmd_extrair = [
                'ffmpeg', '-i', caminho_video,
                '-vf', f'fps={fps_extrair}',
                '-q:v', '2',
                padrao_frame,
                '-y'
            ]
            
            subprocess.run(cmd_extrair, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            
            # Lista frames
            frames = sorted([f for f in os.listdir(pasta_frames) 
                           if f.startswith('frame_') and f.endswith('.jpg')])
            total_frames = len(frames)
            
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {total_frames} frames extraidos")
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Processando frames...")
            
            # Cria pasta para frames editados
            pasta_frames_editados = None
            if aplicar_blur_frames:
                if pasta_saida_frames is None:
                    # Salva na pasta do projeto
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    pasta_frames_editados = os.path.join(script_dir, 'video_frames_editados')
                else:
                    pasta_frames_editados = pasta_saida_frames
                os.makedirs(pasta_frames_editados, exist_ok=True)
                print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Frames editados serao salvos em: {pasta_frames_editados}")
            
            # Reseta agregador temporal
            if not self.use_legacy:
                self.pipeline.reset_temporal_aggregator()
            
            # Processa cada frame
            timestamps_nsfw = []
            timestamps_suggestive = []
            frames_processados = 0
            frames_editados = 0
            
            for i, frame_nome in enumerate(frames):
                caminho_frame = os.path.join(pasta_frames, frame_nome)
                timestamp = i * intervalo_segundos
                
                # Processa frame
                if self.use_legacy:
                    resultado = self.detectar_imagem(caminho_frame)
                    tem_nsfw = resultado.get('tem_nudez', False)
                    confirmed_nudity = tem_nsfw
                    severity = resultado.get('severity', 'NSFW' if tem_nsfw else 'SAFE')
                    resultado_pipeline = resultado  # Para compatibilidade
                else:
                    resultado_frame = self.pipeline.process_video_frame(
                        caminho_frame, i, timestamp
                    )
                    # process_video_frame retorna o resultado do pipeline diretamente (image_result.copy())
                    # Não há uma chave 'pipeline_result' aninhada
                    resultado_pipeline = resultado_frame
                    tem_nsfw = resultado_frame.get('confirmed_nudity', False)
                    confirmed_nudity = tem_nsfw
                    severity = resultado_frame.get('final_severity', 'SAFE')
                    resultado = resultado_frame  # Para compatibilidade com código que usa 'resultado'
                
                if confirmed_nudity:
                    # Aplica blur se solicitado
                    caminho_frame_editado = None
                    if aplicar_blur_frames:
                        # Garante que resultado_pipeline tem severity
                        resultado_para_blur = resultado_pipeline.copy()
                        if 'severity' not in resultado_para_blur:
                            resultado_para_blur['severity'] = severity
                        
                        resultado_blur = self.aplicar_blur(
                            caminho_frame,
                            resultado_para_blur,
                            intensidade_blur=75,
                            pasta_saida=pasta_frames_editados,
                            margem_percentual=40
                        )
                        if resultado_blur.get('aplicado'):
                            caminho_frame_editado = resultado_blur['caminho_saida']
                            frames_editados += 1
                        elif self.debug:
                            print(f"{Fore.YELLOW}[DEBUG] Blur não aplicado no frame {frame_nome}: {resultado_blur.get('mensagem', 'desconhecido')}{Style.RESET_ALL}")
                    
                    timestamps_nsfw.append({
                        'timestamp': timestamp,
                        'tempo_formatado': self._formatar_tempo(timestamp),
                        'confianca': resultado_pipeline.get('confianca', 0.0),
                        'total_deteccoes': resultado_pipeline.get('total_deteccoes', 0),
                        'deteccoes': resultado_pipeline.get('deteccoes', []),
                        'frame': frame_nome,
                        'frame_editado': os.path.basename(caminho_frame_editado) if caminho_frame_editado else None,
                        'caminho_frame_editado': caminho_frame_editado,
                        'severity': resultado_pipeline.get('severity', 'NSFW'),
                        'confirmed': confirmed_nudity
                    })
                elif severity == 'SUGGESTIVE' or (isinstance(severity, str) and severity.upper() == 'SUGGESTIVE'):
                    # Rastreia frames SUGGESTIVE também
                    # Aplica blur também em frames SUGGESTIVE se solicitado
                    caminho_frame_editado = None
                    if aplicar_blur_frames:
                        # Garante que resultado_pipeline tem severity
                        resultado_para_blur = resultado_pipeline.copy()
                        if 'severity' not in resultado_para_blur:
                            resultado_para_blur['severity'] = severity
                        
                        resultado_blur = self.aplicar_blur(
                            caminho_frame,
                            resultado_para_blur,
                            intensidade_blur=75,
                            pasta_saida=pasta_frames_editados,
                            margem_percentual=40
                        )
                        if resultado_blur.get('aplicado'):
                            caminho_frame_editado = resultado_blur['caminho_saida']
                            frames_editados += 1
                        elif self.debug:
                            print(f"{Fore.YELLOW}[DEBUG] Blur não aplicado no frame {frame_nome}: {resultado_blur.get('mensagem', 'desconhecido')}{Style.RESET_ALL}")
                    
                    # Obtém confiança e detecções do resultado apropriado
                    if self.use_legacy:
                        # Modo legacy: confianca está em porcentagem (0-100)
                        confianca_val = resultado_pipeline.get('confianca', 0.0) / 100.0 if resultado_pipeline.get('confianca', 0.0) > 1.0 else resultado_pipeline.get('confianca', 0.0)
                        deteccoes = resultado_pipeline.get('deteccoes', [])
                        total_deteccoes = resultado_pipeline.get('total_deteccoes', len(deteccoes))
                    else:
                        # Modo novo: confidence está em decimal (0-1)
                        confianca_val = resultado_pipeline.get('confidence', 0.0)
                        # Converte parts_detected para formato de detecções
                        parts_detected = resultado_pipeline.get('parts_detected', [])
                        deteccoes = []
                        for part in parts_detected:
                            deteccoes.append({
                                'classe': part.get('class_name', ''),
                                'confianca': round(part.get('score', 0.0) * 100, 2),
                                'bbox': part.get('absolute_bbox', [])
                            })
                        total_deteccoes = len(deteccoes)
                    
                    timestamps_suggestive.append({
                        'timestamp': timestamp,
                        'tempo_formatado': self._formatar_tempo(timestamp),
                        'confianca': confianca_val,
                        'total_deteccoes': total_deteccoes,
                        'deteccoes': deteccoes,
                        'frame': frame_nome,
                        'frame_editado': os.path.basename(caminho_frame_editado) if caminho_frame_editado else None,
                        'caminho_frame_editado': caminho_frame_editado,
                        'severity': 'SUGGESTIVE'
                    })
                
                frames_processados += 1
                if frames_processados % 10 == 0:
                    progresso = (frames_processados / total_frames) * 100
                    print(f"{Fore.CYAN}[PROGRESSO]{Style.RESET_ALL} {frames_processados}/{total_frames} frames ({progresso:.1f}%)")
            
            resultado_final = {
                'erro': False,
                'video': caminho_video,
                'duracao_total': duracao_total,
                'duracao_formatada': self._formatar_tempo(duracao_total),
                'total_frames': total_frames,
                'intervalo_segundos': intervalo_segundos,
                'timestamps_nsfw': timestamps_nsfw,
                'total_cenas_nsfw': len(timestamps_nsfw),
                'timestamps_suggestive': timestamps_suggestive,
                'total_cenas_suggestive': len(timestamps_suggestive),
                'pasta_frames': pasta_frames
            }
            
            if aplicar_blur_frames:
                resultado_final['frames_editados'] = frames_editados
                resultado_final['pasta_frames_editados'] = pasta_frames_editados
            
            if not self.use_legacy:
                resultado_final['temporal_stats'] = self.pipeline.get_temporal_statistics()
            
            return resultado_final
            
        except subprocess.CalledProcessError as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao processar video com ffmpeg: {str(e)}'
            }
        except Exception as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao processar video: {str(e)}'
            }
        finally:
            if pasta_temp and os.path.exists(pasta_temp):
                shutil.rmtree(pasta_temp)
    
    def obter_descricao_nudez_video(self, caminho_video, intervalo_segundos=1.0):
        """
        Analisa vídeo frame a frame e retorna apenas informações textuais sobre a detecção.
        Não processa frames com blur, apenas retorna descrição de onde a nudez aparece.
        
        Args:
            caminho_video (str): Caminho para o vídeo
            intervalo_segundos (float): Intervalo entre frames analisados (padrão: 1.0)
            
        Returns:
            dict: Informações textuais sobre a detecção no vídeo:
                {
                    'tem_nudez': bool,
                    'tipo_nudez': str,  # 'SAFE', 'SUGGESTIVE', 'NSFW' (mais severo encontrado)
                    'descricao_geral': str,  # Descrição geral do vídeo
                    'duracao_total': float,
                    'duracao_formatada': str,
                    'total_frames_processados': int,
                    'timestamps': list,  # Lista de timestamps onde há nudez: [{'timestamp': float, 'tempo_formatado': str, 'tipo_nudez': str, 'descricao': str}, ...]
                    'resumo': dict,  # Estatísticas resumidas
                    'erro': bool,
                    'mensagem': str
                }
        """
        if not os.path.exists(caminho_video):
            return {
                'erro': True,
                'mensagem': f'Vídeo não encontrado: {caminho_video}',
                'tem_nudez': False,
                'tipo_nudez': 'SAFE'
            }
        
        # Verifica ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                'erro': True,
                'mensagem': 'FFmpeg não encontrado. Instale com: sudo apt install ffmpeg',
                'tem_nudez': False,
                'tipo_nudez': 'SAFE'
            }
        
        # Cria pasta temporária
        pasta_temp = tempfile.mkdtemp(prefix='nudez_frames_')
        
        try:
            # Obtém duração do vídeo
            cmd_duracao = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', caminho_video
            ]
            resultado_duracao = subprocess.run(cmd_duracao, 
                                             capture_output=True, 
                                             text=True, 
                                             check=True)
            duracao_total = float(resultado_duracao.stdout.strip())
            
            # Extrai frames
            fps_extrair = 1.0 / intervalo_segundos
            padrao_frame = os.path.join(pasta_temp, 'frame_%06d.jpg')
            
            cmd_extrair = [
                'ffmpeg', '-i', caminho_video,
                '-vf', f'fps={fps_extrair}',
                '-q:v', '2',
                padrao_frame,
                '-y'
            ]
            
            subprocess.run(cmd_extrair, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            
            # Lista frames
            frames = sorted([f for f in os.listdir(pasta_temp) 
                           if f.startswith('frame_') and f.endswith('.jpg')])
            total_frames = len(frames)
            
            # Reseta agregador temporal
            if not self.use_legacy:
                self.pipeline.reset_temporal_aggregator()
            
            # Processa cada frame (sem aplicar blur)
            timestamps_info = []
            frames_processados = 0
            tipo_nudez_max = 'SAFE'  # Rastreia o tipo mais severo encontrado
            
            for i, frame_nome in enumerate(frames):
                caminho_frame = os.path.join(pasta_temp, frame_nome)
                timestamp = i * intervalo_segundos
                
                # Processa frame
                if self.use_legacy:
                    resultado = self.detectar_imagem(caminho_frame)
                    tem_nudez = resultado.get('tem_nudez', False)
                    severity = resultado.get('severity', 'SAFE')
                    resultado_pipeline = resultado
                else:
                    resultado_frame = self.pipeline.process_video_frame(
                        caminho_frame, i, timestamp
                    )
                    resultado_pipeline = resultado_frame
                    tem_nudez = resultado_frame.get('confirmed_nudity', False)
                    severity = resultado_frame.get('final_severity', 'SAFE')
                
                # Se há detecção, adiciona informação textual
                if tem_nudez or severity in ['SUGGESTIVE', 'NSFW']:
                    # Obtém descrição do frame
                    if self.use_legacy:
                        descricao_frame = self._gerar_descricao_frame_legacy(resultado_pipeline)
                    else:
                        descricao_frame = self._gerar_descricao_frame(resultado_frame)
                    
                    # Atualiza tipo máximo
                    if severity == 'NSFW':
                        tipo_nudez_max = 'NSFW'
                    elif severity == 'SUGGESTIVE' and tipo_nudez_max != 'NSFW':
                        tipo_nudez_max = 'SUGGESTIVE'
                    
                    timestamps_info.append({
                        'timestamp': timestamp,
                        'tempo_formatado': self._formatar_tempo(timestamp),
                        'tipo_nudez': severity,
                        'descricao': descricao_frame
                    })
                
                frames_processados += 1
            
            # Obtém estatísticas do agregador temporal
            estatisticas = {}
            if not self.use_legacy:
                stats = self.pipeline.temporal_aggregator.get_statistics()
                estatisticas = {
                    'total_frames_nsfw': stats.get('nsfw_frames', 0),
                    'total_frames_suggestive': stats.get('suggestive_frames', 0),
                    'total_frames_safe': stats.get('safe_frames', 0),
                    'total_frames_processados': stats.get('total_frames', 0)
                }
            else:
                estatisticas = {
                    'total_frames_processados': frames_processados
                }
            
            # Gera descrição geral
            descricao_geral = self._gerar_descricao_geral_video(
                tipo_nudez_max, 
                len(timestamps_info), 
                total_frames,
                estatisticas
            )
            
            return {
                'erro': False,
                'tem_nudez': len(timestamps_info) > 0,
                'tipo_nudez': tipo_nudez_max,
                'descricao_geral': descricao_geral,
                'duracao_total': duracao_total,
                'duracao_formatada': self._formatar_tempo(duracao_total),
                'total_frames_processados': frames_processados,
                'timestamps': timestamps_info,
                'resumo': estatisticas
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao processar vídeo com ffmpeg: {str(e)}',
                'tem_nudez': False,
                'tipo_nudez': 'SAFE'
            }
        except Exception as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao processar vídeo: {str(e)}',
                'tem_nudez': False,
                'tipo_nudez': 'SAFE'
            }
        finally:
            # Limpa pasta temporária
            if os.path.exists(pasta_temp):
                shutil.rmtree(pasta_temp)
    
    def _gerar_descricao_frame(self, resultado_frame):
        """Gera descrição textual de um frame processado."""
        severity_result = resultado_frame.get('severity_result', {})
        reason = severity_result.get('reason', '')
        severity = resultado_frame.get('final_severity', 'SAFE')
        
        parts = resultado_frame.get('parts_detected', [])
        partes_por_tipo = {}
        
        for part in parts:
            classe = part.get('class_name', '').upper()
            tipo = 'outro'
            if 'BREAST' in classe:
                tipo = 'seios'
            elif 'NIPPLE' in classe:
                tipo = 'mamilos'
            elif 'GENITALIA' in classe or 'GENITAL' in classe:
                tipo = 'genitália'
            elif 'ANUS' in classe:
                tipo = 'ânus'
            elif 'BUTTOCK' in classe:
                tipo = 'nádegas'
            
            if tipo not in partes_por_tipo:
                partes_por_tipo[tipo] = []
            partes_por_tipo[tipo].append(classe)
        
        desc_parts = []
        if 'genitália' in partes_por_tipo:
            desc_parts.append('genitália exposta')
        if 'ânus' in partes_por_tipo:
            desc_parts.append('ânus exposto')
        if 'mamilos' in partes_por_tipo:
            desc_parts.append('mamilos expostos')
        if 'seios' in partes_por_tipo and 'mamilos' not in partes_por_tipo:
            desc_parts.append('seios expostos sem mamilos visíveis')
        elif 'seios' in partes_por_tipo:
            desc_parts.append('seios expostos')
        if 'nádegas' in partes_por_tipo:
            desc_parts.append('nádegas expostas')
        
        if desc_parts:
            descricao = f"{', '.join(desc_parts)}. {reason}" if reason else ', '.join(desc_parts)
        else:
            descricao = reason if reason else 'Conteúdo detectado'
        
        return descricao
    
    def _gerar_descricao_frame_legacy(self, resultado):
        """Gera descrição textual de um frame (modo legacy)."""
        deteccoes = resultado.get('deteccoes', [])
        partes = set()
        
        for det in deteccoes:
            classe = det.get('classe', '').upper()
            if 'BREAST' in classe:
                partes.add('seios')
            if 'NIPPLE' in classe:
                partes.add('mamilos')
            if 'GENITALIA' in classe or 'GENITAL' in classe:
                partes.add('genitália')
            if 'ANUS' in classe:
                partes.add('ânus')
            if 'BUTTOCK' in classe:
                partes.add('nádegas')
        
        if partes:
            return f"{', '.join(partes)} detectados"
        return "Conteúdo sensível detectado"
    
    def _extrair_partes_detectadas(self, resultado):
        """Extrai lista de partes detectadas do resultado."""
        parts = resultado.get('parts_detected', [])
        if not parts:
            deteccoes = resultado.get('deteccoes', [])
            return [d.get('classe', '') for d in deteccoes if d.get('classe')]
        return [p.get('class_name', '') for p in parts if p.get('class_name')]
    
    def _gerar_descricao_geral_video(self, tipo_nudez, num_timestamps, total_frames, estatisticas):
        """Gera descrição geral do vídeo."""
        if tipo_nudez == 'SAFE':
            return f'Nenhum conteúdo sensível detectado no vídeo ({total_frames} frames processados).'
        
        porcentagem = (num_timestamps / total_frames * 100) if total_frames > 0 else 0
        
        if tipo_nudez == 'NSFW':
            return f'Conteúdo explícito (NSFW) detectado em {num_timestamps} timestamp(s) ({porcentagem:.1f}% do vídeo).'
        elif tipo_nudez == 'SUGGESTIVE':
            return f'Conteúdo sugestivo detectado em {num_timestamps} timestamp(s) ({porcentagem:.1f}% do vídeo).'
        
        return f'Conteúdo detectado em {num_timestamps} timestamp(s).'
    
    def _formatar_tempo(self, segundos):
        """Formata segundos em formato HH:MM:SS"""
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segs = int(segundos % 60)
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"
    
    def aplicar_blur(self, caminho_imagem, resultado_deteccao, 
                     intensidade_blur=75, pasta_saida=None, margem_percentual=40):
        """
        Aplica blur nas áreas onde foi detectado conteúdo NSFW
        
        Args:
            caminho_imagem (str): Caminho para a imagem original
            resultado_deteccao (dict): Resultado da detecção
            intensidade_blur (int): Intensidade do blur (deve ser ímpar)
            pasta_saida (str): Pasta para salvar a imagem processada
            margem_percentual (float): Margem percentual para expandir o blur
            
        Returns:
            dict: Resultado com caminho da imagem processada
        """
        # Verifica severity para decidir se aplica blur
        # Tenta obter severity diretamente ou de dentro de pipeline_result
        severity = resultado_deteccao.get('severity', None)
        if severity is None:
            severity = resultado_deteccao.get('pipeline_result', {}).get('severity', 'SAFE')
        if severity == SeverityLevel.SAFE.value or severity == 'SAFE':
            return {
                'erro': False,
                'aplicado': False,
                'mensagem': 'Nenhum conteúdo sensível detectado, blur não aplicado'
            }
        
        # Verifica se há erro ou se não detectou nudez/conteúdo sensível
        if resultado_deteccao.get('erro'):
            return {
                'erro': True,
                'aplicado': False,
                'mensagem': 'Erro na detecção, blur não aplicado'
            }
        
        # Se não tem tem_nudez mas tem severity SUGGESTIVE ou NSFW, ainda aplica blur
        tem_nudez = resultado_deteccao.get('tem_nudez', resultado_deteccao.get('nudity_detected', False))
        severity_values = [SeverityLevel.SUGGESTIVE.value, SeverityLevel.NSFW.value, 'SUGGESTIVE', 'NSFW']
        if not tem_nudez and severity not in severity_values:
            return {
                'erro': False,
                'aplicado': False,
                'mensagem': 'Nenhum conteúdo sensível detectado, blur não aplicado'
            }
        
        try:
            # Garante que intensidade_blur seja ímpar
            if intensidade_blur % 2 == 0:
                intensidade_blur += 1
            
            # Carrega imagem
            imagem = cv2.imread(caminho_imagem)
            if imagem is None:
                return {
                    'erro': True,
                    'mensagem': 'Erro ao carregar imagem com OpenCV'
                }
            
            altura, largura = imagem.shape[:2]
            areas_processadas = 0
            
            # Obtém partes detectadas
            # Tenta primeiro obter diretamente (quando resultado_deteccao é o pipeline_result)
            parts = resultado_deteccao.get('parts_detected', [])
            if not parts:
                # Tenta dentro de pipeline_result (quando resultado_deteccao é o resultado completo)
                parts = resultado_deteccao.get('pipeline_result', {}).get('parts_detected', [])
            if not parts:
                # Fallback para formato antigo (legacy)
                parts = resultado_deteccao.get('deteccoes', [])
            
            # Se não há partes detectadas, retorna sem aplicar blur
            if not parts:
                return {
                    'erro': False,
                    'aplicado': False,
                    'mensagem': f'Nenhuma parte detectada encontrada (severity: {severity})'
                }
            
            # Aplica blur em cada área detectada
            # FILTRA apenas partes sensíveis (não faces, braços, axilas, etc.)
            partes_sensiveis = ['breast', 'genitalia', 'nipple', 'buttocks', 'anus']
            partes_a_ignorar = ['face', 'armpit', 'belly', 'other']  # Partes que NÃO devem receber blur
            
            for deteccao in parts:
                # Verifica se é uma parte sensível
                class_name = ''
                if isinstance(deteccao, dict):
                    class_name = deteccao.get('class_name', '').upper()
                    anatomical_type = deteccao.get('anatomical_type', '').lower()
                    
                    # Filtra: ignora faces, braços, axilas, etc. Aplica blur APENAS em partes sensíveis
                    if anatomical_type in partes_a_ignorar:
                        # Verifica se não é uma exceção (ex: pode ter "breast" no nome mas anatomical_type="other")
                        if not any(sensivel in class_name for sensivel in ['BREAST', 'GENITALIA', 'NIPPLE', 'BUTTOCKS', 'ANUS']):
                            continue  # Pula esta detecção - não é parte sensível
                    
                    # Se anatomical_type não está em partes_sensiveis, verifica pelo nome da classe
                    if anatomical_type not in partes_sensiveis:
                        # Verifica se o nome da classe indica parte sensível
                        if not any(sensivel in class_name for sensivel in ['BREAST', 'GENITALIA', 'NIPPLE', 'BUTTOCKS', 'ANUS', 'EXPOSED_BUTTOCKS', 'EXPOSED_GENITALIA', 'EXPOSED_BREAST', 'FEMALE_BREAST', 'MALE_BREAST']):
                            continue  # Pula esta detecção - não é parte sensível
                    
                    # PREFERE absolute_bbox sempre que disponível (já está em formato [x1, y1, x2, y2])
                    absolute_bbox = deteccao.get('absolute_bbox')
                    bbox_original = deteccao.get('bbox') or deteccao.get('box')
                    bbox = absolute_bbox if absolute_bbox else bbox_original
                    usando_absolute_bbox = absolute_bbox is not None
                else:
                    anatomical_type = getattr(deteccao, 'anatomical_type', '').lower()
                    class_name = getattr(deteccao, 'class_name', '').upper()
                    
                    # Mesma lógica para objetos
                    if anatomical_type in partes_a_ignorar:
                        if not any(sensivel in class_name for sensivel in ['BREAST', 'GENITALIA', 'NIPPLE', 'BUTTOCKS', 'ANUS']):
                            continue
                    if anatomical_type not in partes_sensiveis:
                        if not any(sensivel in class_name for sensivel in ['BREAST', 'GENITALIA', 'NIPPLE', 'BUTTOCKS', 'ANUS']):
                            continue
                    
                    absolute_bbox = getattr(deteccao, 'absolute_bbox', None)
                    bbox_original = getattr(deteccao, 'bbox', None)
                    bbox = absolute_bbox if absolute_bbox else bbox_original
                    usando_absolute_bbox = absolute_bbox is not None
                
                if bbox and len(bbox) >= 4:
                    try:
                        bbox_values = [float(v) for v in bbox[:4]]
                        temp_x1, temp_y1, temp_x2, temp_y2 = bbox_values
                        
                        # Detecta formato: se x2 <= x1 OU y2 <= y1, é [x, y, width, height]
                        # Mesmo que seja absolute_bbox, se está inválido, pode estar em formato errado
                        if temp_x2 <= temp_x1 or temp_y2 <= temp_y1:
                            # Formato [x, y, width, height] - NudeNet padrão
                            x, y, w, h = bbox_values
                            x1, y1 = int(x), int(y)
                            x2, y2 = int(x + w), int(y + h)
                        else:
                            # Formato [x1, y1, x2, y2] - já está correto
                            x1, y1, x2, y2 = [int(v) for v in bbox_values]
                        
                        # Valida que x2 > x1 e y2 > y1 (bbox válido)
                        if x2 <= x1 or y2 <= y1:
                            if self.debug:
                                print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Bbox inválido após conversão: [{x1}, {y1}, {x2}, {y2}] (original: {bbox_values}, usando_absolute: {usando_absolute_bbox})")
                            continue
                        
                        # Calcula dimensões
                        bbox_largura = x2 - x1
                        bbox_altura = y2 - y1
                        
                        # Para seios expostos, usa margem maior para garantir cobertura completa
                        # mesmo quando mamilos não estão explicitamente visíveis
                        margem_ajustada = margem_percentual
                        if 'BREAST' in class_name and 'NIPPLE' not in class_name:
                            # Seios sem mamilos detectados - aumenta margem para cobrir melhor
                            margem_ajustada = margem_percentual * 1.5  # 50% mais margem
                        
                        # Adiciona margem
                        margem_x = max(bbox_largura * (margem_ajustada / 100.0), 30)
                        margem_y = max(bbox_altura * (margem_ajustada / 100.0), 30)
                        
                        # Expande bbox
                        x1_expandido = max(0, int(x1 - margem_x))
                        y1_expandido = max(0, int(y1 - margem_y))
                        x2_expandido = min(largura, int(x2 + margem_x))
                        y2_expandido = min(altura, int(y2 + margem_y))
                        
                        # Valida região expandida
                        if x2_expandido > x1_expandido and y2_expandido > y1_expandido:
                            # Garante que está dentro dos limites da imagem
                            x1_expandido = max(0, min(x1_expandido, largura - 1))
                            y1_expandido = max(0, min(y1_expandido, altura - 1))
                            x2_expandido = max(x1_expandido + 1, min(x2_expandido, largura))
                            y2_expandido = max(y1_expandido + 1, min(y2_expandido, altura))
                            
                            # Extrai região
                            try:
                                regiao = imagem[y1_expandido:y2_expandido, x1_expandido:x2_expandido].copy()
                                
                                if regiao.size == 0:
                                    if self.debug:
                                        print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Região vazia após extração: [{x1_expandido}, {y1_expandido}, {x2_expandido}, {y2_expandido}]")
                                    continue
                                
                                # Calcula blur baseado no tamanho
                                regiao_largura = x2_expandido - x1_expandido
                                regiao_altura = y2_expandido - y1_expandido
                                blur_base = max(25, int(min(regiao_largura, regiao_altura) * 0.4))
                                blur_ajustado = min(intensidade_blur, blur_base)
                                if blur_ajustado % 2 == 0:
                                    blur_ajustado = max(1, blur_ajustado - 1)
                                
                                # Aplica blur múltiplas vezes
                                regiao_blur = cv2.GaussianBlur(regiao, (blur_ajustado, blur_ajustado), 0)
                                regiao_blur = cv2.GaussianBlur(regiao_blur, (blur_ajustado, blur_ajustado), 0)
                                blur_final = max(15, blur_ajustado - 10) if blur_ajustado > 15 else blur_ajustado
                                if blur_final % 2 == 0:
                                    blur_final = max(1, blur_final - 1)
                                regiao_blur = cv2.GaussianBlur(regiao_blur, (blur_final, blur_final), 0)
                                
                                if blur_ajustado >= 30:
                                    blur_extra = blur_ajustado + 10
                                    if blur_extra % 2 == 0:
                                        blur_extra += 1
                                    regiao_blur = cv2.GaussianBlur(regiao_blur, (blur_extra, blur_extra), 0)
                                
                                # Substitui região
                                imagem[y1_expandido:y2_expandido, x1_expandido:x2_expandido] = regiao_blur
                                areas_processadas += 1
                                
                                if self.debug:
                                    print(f"{Fore.GREEN}[DEBUG]{Style.RESET_ALL} Blur aplicado: {class_name} [{x1}, {y1}, {x2}, {y2}] -> expandido [{x1_expandido}, {y1_expandido}, {x2_expandido}, {y2_expandido}]")
                                
                            except (ValueError, TypeError, IndexError) as e:
                                if self.debug:
                                    print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Erro ao extrair/aplicar blur na região [{x1_expandido}, {y1_expandido}, {x2_expandido}, {y2_expandido}]: {e}")
                                continue
                        else:
                            if self.debug:
                                print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Região expandida inválida: [{x1_expandido}, {y1_expandido}, {x2_expandido}, {y2_expandido}] (bbox original: [{x1}, {y1}, {x2}, {y2}])")
                            
                    except (ValueError, TypeError, IndexError) as e:
                        if self.debug:
                            print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Erro ao processar bbox {bbox_values} ({class_name}): {e}")
                        continue
            
            # Define caminho de saída
            if pasta_saida:
                os.makedirs(pasta_saida, exist_ok=True)
                nome_arquivo = os.path.basename(caminho_imagem)
                caminho_saida = os.path.join(pasta_saida, f"blur_{nome_arquivo}")
            else:
                diretorio = os.path.dirname(caminho_imagem)
                nome_arquivo = os.path.basename(caminho_imagem)
                caminho_saida = os.path.join(diretorio, f"blur_{nome_arquivo}")
            
            # Salva imagem
            extensao = Path(caminho_saida).suffix.lower()
            if extensao in ['.jpg', '.jpeg']:
                cv2.imwrite(caminho_saida, imagem, [cv2.IMWRITE_JPEG_QUALITY, 95])
            elif extensao == '.png':
                cv2.imwrite(caminho_saida, imagem, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            else:
                cv2.imwrite(caminho_saida, imagem)
            
            if areas_processadas > 0:
                return {
                    'erro': False,
                    'aplicado': True,
                    'caminho_saida': caminho_saida,
                    'total_areas_blur': areas_processadas,
                    'margem_usada': margem_percentual
                }
            else:
                return {
                    'erro': True,
                    'mensagem': 'Nenhuma área válida foi processada com blur'
                }
            
        except Exception as e:
            return {
                'erro': True,
                'mensagem': f'Erro ao aplicar blur: {str(e)}'
            }


# Funções de impressão (mantidas para compatibilidade)
def imprimir_resultado(resultado, resultado_blur=None):
    """Imprime o resultado da detecção de forma formatada com cores"""
    if resultado.get('erro'):
        print(f"{Fore.RED}{Style.BRIGHT}[ERRO]{Style.RESET_ALL} {resultado['mensagem']}")
        return
    
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{Style.BRIGHT}Imagem:{Style.RESET_ALL} {Fore.YELLOW}{os.path.basename(resultado['caminho'])}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    # Mostra informações do pipeline
    if resultado.get('humans_detected') is not None:
        print(f"{Fore.CYAN}Humanos detectados:{Style.RESET_ALL} {Fore.WHITE}{resultado['humans_detected']}{Style.RESET_ALL}")
    
    severity = resultado.get('severity', 'SAFE')
    tem_nudez = resultado.get('tem_nudez', False)
    
    if tem_nudez or severity != 'SAFE':
        print(f"{Fore.RED}{Back.RED}{Style.BRIGHT} CONTEUDO {severity} DETECTADO! {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}Severidade:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{severity}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}Confianca maxima:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{resultado['confianca']}%{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}Total de deteccoes:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{resultado['total_deteccoes']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Threshold usado:{Style.RESET_ALL} {Fore.WHITE}{resultado.get('threshold_usado', 'N/A')}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Detalhes das deteccoes:{Style.RESET_ALL}")
        for i, det in enumerate(resultado['deteccoes'], 1):
            print(f"  {Fore.WHITE}{i}.{Style.RESET_ALL} {Fore.RED}{det['classe']}{Style.RESET_ALL}: {Fore.YELLOW}{det['confianca']}%{Style.RESET_ALL}")
        
        if resultado_blur:
            if resultado_blur.get('aplicado'):
                print(f"\n{Fore.GREEN}{Style.BRIGHT}[SUCESSO]{Style.RESET_ALL} Blur aplicado com sucesso!")
                print(f"{Fore.CYAN}Imagem salva em:{Style.RESET_ALL} {Fore.WHITE}{resultado_blur['caminho_saida']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Areas com blur:{Style.RESET_ALL} {Fore.GREEN}{resultado_blur['total_areas_blur']}{Style.RESET_ALL}")
            elif resultado_blur.get('erro'):
                print(f"\n{Fore.RED}{Style.BRIGHT}[ERRO]{Style.RESET_ALL} Erro ao aplicar blur: {resultado_blur['mensagem']}")
    else:
        print(f"{Fore.GREEN}{Style.BRIGHT}[SEGURO]{Style.RESET_ALL} Nenhum conteudo NSFW detectado")
        print(f"{Fore.CYAN}Threshold usado:{Style.RESET_ALL} {Fore.WHITE}{resultado.get('threshold_usado', 'N/A')}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}A imagem parece ser segura.{Style.RESET_ALL}")


def imprimir_resultado_video(resultado_video):
    """Imprime o resultado do processamento de vídeo de forma formatada"""
    if resultado_video.get('erro'):
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} {resultado_video['mensagem']}")
        return
    
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{Style.BRIGHT}Video:{Style.RESET_ALL} {Fore.YELLOW}{os.path.basename(resultado_video['video'])}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}Duracao total:{Style.RESET_ALL} {Fore.WHITE}{resultado_video['duracao_formatada']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total de frames processados:{Style.RESET_ALL} {Fore.WHITE}{resultado_video['total_frames']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Intervalo entre frames:{Style.RESET_ALL} {Fore.WHITE}{resultado_video['intervalo_segundos']} segundo(s){Style.RESET_ALL}")
    
    if resultado_video.get('frames_editados'):
        print(f"{Fore.GREEN}{Style.BRIGHT}Frames editados com blur:{Style.RESET_ALL} {Fore.GREEN}{resultado_video['frames_editados']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Pasta dos frames editados:{Style.RESET_ALL} {Fore.WHITE}{resultado_video['pasta_frames_editados']}{Style.RESET_ALL}")
    
    if resultado_video.get('temporal_stats'):
        stats = resultado_video['temporal_stats']
        print(f"{Fore.CYAN}Estatisticas temporais:{Style.RESET_ALL}")
        print(f"  Frames NSFW: {stats.get('nsfw_frames', 0)}/{stats.get('total_frames', 0)}")
        print(f"  Frames SUGGESTIVE: {stats.get('suggestive_frames', 0)}/{stats.get('total_frames', 0)}")
        print(f"  Frames SAFE: {stats.get('safe_frames', 0)}/{stats.get('total_frames', 0)}")
        print(f"  Frames consecutivos NSFW: {stats.get('consecutive_nsfw', 0)}")
        print(f"  Score acumulado: {stats.get('accumulated_score', 0.0):.2f}")
    
    if resultado_video['total_cenas_nsfw'] > 0:
        print(f"\n{Fore.RED}{Back.RED}{Style.BRIGHT} CONTEUDO NSFW DETECTADO! {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}Total de cenas com NSFW:{Style.RESET_ALL} {Fore.RED}{resultado_video['total_cenas_nsfw']}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Timestamps com conteudo NSFW:{Style.RESET_ALL}\n")
        
        for i, cena in enumerate(resultado_video['timestamps_nsfw'], 1):
            print(f"{Fore.WHITE}{i}.{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}Timestamp:{Style.RESET_ALL} {Fore.YELLOW}{cena['tempo_formatado']}{Style.RESET_ALL} ({cena['timestamp']:.2f}s)")
            print(f"   {Fore.CYAN}Severidade:{Style.RESET_ALL} {Fore.RED}{cena.get('severity', 'NSFW')}{Style.RESET_ALL}")
            confianca_display = cena['confianca']
            if isinstance(confianca_display, float) and confianca_display <= 1.0:
                confianca_display = f"{confianca_display * 100:.1f}%"
            else:
                confianca_display = f"{confianca_display:.1f}%"
            print(f"   {Fore.CYAN}Confianca:{Style.RESET_ALL} {Fore.RED}{confianca_display}{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}Deteccoes:{Style.RESET_ALL} {Fore.RED}{cena['total_deteccoes']}{Style.RESET_ALL}")
            if cena.get('confirmed'):
                print(f"   {Fore.GREEN}Confirmado temporalmente:{Style.RESET_ALL} {Fore.GREEN}Sim{Style.RESET_ALL}")
            if cena.get('frame_editado'):
                print(f"   {Fore.GREEN}Frame editado:{Style.RESET_ALL} {Fore.WHITE}{cena['frame_editado']}{Style.RESET_ALL}")
            print()
    elif resultado_video.get('total_cenas_suggestive', 0) > 0:
        # Considera conteúdo sensível se houver muitos frames SUGGESTIVE
        total_suggestive = resultado_video['total_cenas_suggestive']
        total_frames = resultado_video['total_frames']
        suggestive_ratio = total_suggestive / total_frames if total_frames > 0 else 0.0
        
        if suggestive_ratio >= 0.3:  # 30% ou mais do vídeo é sugestivo
            print(f"\n{Fore.YELLOW}{Back.YELLOW}{Style.BRIGHT} CONTEUDO SUGESTIVO DETECTADO! {Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{Style.BRIGHT}Total de frames sugestivos:{Style.RESET_ALL} {Fore.YELLOW}{total_suggestive}/{total_frames} ({suggestive_ratio:.1%}){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}O video contem conteudo sugestivo (seios sem mamilos, etc.){Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}Timestamps com conteudo sugestivo:{Style.RESET_ALL}\n")
            
            # Mostra apenas alguns exemplos (primeiros 10)
            for i, cena in enumerate(resultado_video['timestamps_suggestive'][:10], 1):
                print(f"{Fore.WHITE}{i}.{Style.RESET_ALL} {Fore.YELLOW}{Style.BRIGHT}Timestamp:{Style.RESET_ALL} {Fore.WHITE}{cena['tempo_formatado']}{Style.RESET_ALL} ({cena['timestamp']:.2f}s)")
                confianca_display = cena['confianca']
                if isinstance(confianca_display, float) and confianca_display <= 1.0:
                    confianca_display = f"{confianca_display * 100:.1f}%"
                else:
                    confianca_display = f"{confianca_display:.1f}%"
                print(f"   {Fore.CYAN}Confianca:{Style.RESET_ALL} {Fore.YELLOW}{confianca_display}{Style.RESET_ALL}")
                print(f"   {Fore.CYAN}Deteccoes:{Style.RESET_ALL} {Fore.YELLOW}{cena['total_deteccoes']}{Style.RESET_ALL}")
                print()
            
            if len(resultado_video['timestamps_suggestive']) > 10:
                print(f"{Fore.YELLOW}... e mais {len(resultado_video['timestamps_suggestive']) - 10} timestamps sugestivos{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}[SEGURO]{Style.RESET_ALL} Nenhum conteudo NSFW detectado no video")
            print(f"{Fore.GREEN}O video parece ser seguro.{Style.RESET_ALL}")
            if total_suggestive > 0:
                print(f"{Fore.YELLOW}(Nota: {total_suggestive} frames sugestivos detectados, mas abaixo do threshold){Style.RESET_ALL}")
    else:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}[SEGURO]{Style.RESET_ALL} Nenhum conteudo NSFW detectado no video")
        print(f"{Fore.GREEN}O video parece ser seguro.{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


def main():
    """Função principal"""
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}  DETECTOR DE NUDEZ - Pipeline Multiestágio v2.0{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    # Processa argumentos
    aplicar_blur = False
    intensidade_blur = 75
    pasta_saida = None
    caminho = None
    threshold = 0.30
    debug = False
    margem_blur = 40
    processar_video = False
    intervalo_video = 1.0
    use_legacy = False
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ['--blur', '-b']:
            aplicar_blur = True
            i += 1
        elif arg in ['--intensidade', '-i']:
            if i + 1 < len(sys.argv):
                try:
                    intensidade_blur = int(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Intensidade do blur deve ser um numero")
                    sys.exit(1)
            else:
                print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} --intensidade requer um valor")
                sys.exit(1)
        elif arg in ['--saida', '-o']:
            if i + 1 < len(sys.argv):
                pasta_saida = sys.argv[i + 1]
                i += 2
            else:
                print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} --saida requer um caminho")
                sys.exit(1)
        elif arg in ['--threshold', '-t']:
            if i + 1 < len(sys.argv):
                try:
                    threshold = float(sys.argv[i + 1])
                    if not 0.0 <= threshold <= 1.0:
                        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Threshold deve estar entre 0.0 e 1.0")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Threshold deve ser um numero entre 0.0 e 1.0")
                    sys.exit(1)
            else:
                print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} --threshold requer um valor")
                sys.exit(1)
        elif arg in ['--debug', '-d']:
            debug = True
            i += 1
        elif arg in ['--margem', '-m']:
            if i + 1 < len(sys.argv):
                try:
                    margem_blur = float(sys.argv[i + 1])
                    if margem_blur < 0 or margem_blur > 100:
                        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Margem deve estar entre 0 e 100")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Margem deve ser um numero")
                    sys.exit(1)
            else:
                print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} --margem requer um valor")
                sys.exit(1)
        elif arg in ['--video', '-v']:
            processar_video = True
            i += 1
        elif arg in ['--intervalo', '--fps']:
            if i + 1 < len(sys.argv):
                try:
                    intervalo_video = float(sys.argv[i + 1])
                    if intervalo_video <= 0:
                        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Intervalo deve ser maior que 0")
                        sys.exit(1)
                    i += 2
                except ValueError:
                    print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Intervalo deve ser um numero")
                    sys.exit(1)
            else:
                print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} --intervalo requer um valor")
                sys.exit(1)
        elif arg in ['--legacy']:
            use_legacy = True
            i += 1
        elif arg in ['--help', '-h']:
            print("\nUso:")
            print(f"  python3 {sys.argv[0]} [opções] <caminho_imagem>")
            print(f"  python3 {sys.argv[0]} [opções] <caminho_pasta>")
            print(f"  python3 {sys.argv[0]} --video [opções] <caminho_video>")
            print("\nOpções:")
            print("  --blur, -b              Aplica blur nas áreas detectadas")
            print("  --intensidade, -i NUM   Intensidade do blur (ímpar, padrão: 75)")
            print("  --margem, -m NUM       Margem de expansão do blur em % (0-100, padrão: 40)")
            print("  --saida, -o CAMINHO     Pasta para salvar imagens processadas")
            print("  --threshold, -t NUM     Threshold de confiança (0.0-1.0, padrão: 0.30)")
            print("  --debug, -d             Mostra todas as detecções (modo debug)")
            print("  --video, -v             Processa um vídeo (extrai frames e detecta nudez)")
            print("  --intervalo NUM         Intervalo entre frames em segundos (padrão: 1.0)")
            print("  --legacy                Usa implementação antiga (não recomendado)")
            print("  --help, -h              Mostra esta ajuda")
            print("\nExemplos:")
            print(f"  python3 {sys.argv[0]} foto.jpg")
            print(f"  python3 {sys.argv[0]} --blur foto.jpg")
            print(f"  python3 {sys.argv[0]} --threshold 0.2 foto.jpg")
            print(f"  python3 {sys.argv[0]} --debug foto.jpg")
            print(f"  python3 {sys.argv[0]} --video video.mp4")
            sys.exit(0)
        else:
            if caminho is None:
                caminho = arg
            i += 1
    
    # Inicializa o detector
    detector = DetectorNudez(threshold=threshold, debug=debug, use_legacy=use_legacy)
    
    if caminho is None:
        print(f"\n{Fore.RED}[ERRO]{Style.RESET_ALL} Caminho da imagem, pasta ou video nao especificado")
        print(f"{Fore.YELLOW}Use --help para ver as opcoes disponiveis{Style.RESET_ALL}")
        sys.exit(1)
    
    # Processa vídeo
    if processar_video:
        if not os.path.isfile(caminho):
            print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Arquivo de video nao encontrado: {caminho}")
            sys.exit(1)
        
        resultado_video = detector.processar_video(caminho, intervalo_video, aplicar_blur_frames=aplicar_blur)
        imprimir_resultado_video(resultado_video)
        sys.exit(0)
    
    # Detecta se é arquivo ou pasta
    if os.path.isfile(caminho):
        resultado = detector.detectar_imagem(caminho)
        resultado_blur = None
        
        if aplicar_blur:
            resultado_blur = detector.aplicar_blur(
                caminho, resultado, intensidade_blur, pasta_saida, margem_blur
            )
        
        imprimir_resultado(resultado, resultado_blur)
        
    elif os.path.isdir(caminho):
        resultados = detector.detectar_pasta(caminho)
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}RESUMO:{Style.RESET_ALL} {Fore.WHITE}{len(resultados)}{Style.RESET_ALL} imagens processadas")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        total_nsfw = sum(1 for r in resultados 
                        if r.get('tem_nudez', False) or 
                           r.get('severity', 'SAFE') != 'SAFE')
        print(f"{Fore.RED}{Style.BRIGHT}Imagens com NSFW:{Style.RESET_ALL} {Fore.RED}{total_nsfw}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{Style.BRIGHT}Imagens seguras:{Style.RESET_ALL} {Fore.GREEN}{len(resultados) - total_nsfw}{Style.RESET_ALL}")
        
        if aplicar_blur:
            print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} Aplicando blur nas imagens detectadas...")
            total_blur = 0
            for resultado in resultados:
                if resultado.get('tem_nudez') or resultado.get('severity', 'SAFE') != 'SAFE':
                    resultado_blur = detector.aplicar_blur(
                        resultado['caminho'], 
                        resultado, 
                        intensidade_blur, 
                        pasta_saida,
                        margem_blur
                    )
                    if resultado_blur.get('aplicado'):
                        total_blur += 1
            print(f"{Fore.GREEN}{Style.BRIGHT}[SUCESSO]{Style.RESET_ALL} {total_blur} imagens processadas com blur")
        
        print("\nDetalhes por imagem:")
        for resultado in resultados:
            imprimir_resultado(resultado)
    else:
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Caminho invalido: {caminho}")
        sys.exit(1)


if __name__ == "__main__":
    main()

