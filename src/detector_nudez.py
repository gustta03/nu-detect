
"""
Aplicação para detecção de nudez em imagens usando NudeNet
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
    from nudenet import NudeDetector
except ImportError:
    print(f"{Fore.RED}Erro: Biblioteca nudenet não encontrada.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Execute: pip install -r requirements.txt{Style.RESET_ALL}")
    sys.exit(1)


class DetectorNudez:
    """Classe para detectar conteúdo NSFW em imagens"""



    CLASSES_NSFW = [

        'EXPOSED_ANUS', 'ANUS_EXPOSED',
        'EXPOSED_GENITALIA_F', 'EXPOSED_GENITALIA_M',
        'GENITALIA_F_EXPOSED', 'GENITALIA_M_EXPOSED',
        'FEMALE_GENITALIA_EXPOSED', 'MALE_GENITALIA_EXPOSED',

        'EXPOSED_BREAST_F', 'EXPOSED_BREAST_M',
        'BREAST_F_EXPOSED', 'BREAST_M_EXPOSED',
        'FEMALE_BREAST_EXPOSED', 'MALE_BREAST_EXPOSED',
        'EXPOSED_NIPPLES_F', 'EXPOSED_NIPPLES_M',
        'NIPPLES_F_EXPOSED', 'NIPPLES_M_EXPOSED',

        'EXPOSED_BUTTOCKS', 'BUTTOCKS_EXPOSED'
    ]


    CLASSES_CRITICAS = [
        'EXPOSED_ANUS', 'ANUS_EXPOSED',
        'EXPOSED_GENITALIA_F', 'EXPOSED_GENITALIA_M',
        'GENITALIA_F_EXPOSED', 'GENITALIA_M_EXPOSED',
        'FEMALE_GENITALIA_EXPOSED', 'MALE_GENITALIA_EXPOSED'
    ]

    def __init__(self, threshold=0.20, debug=False):
        """
        Inicializa o detector

        Args:
            threshold (float): Threshold de confiança mínimo (0.0 a 1.0, padrão: 0.3)
            debug (bool): Se True, mostra todas as detecções, mesmo não-NSFW
        """
        print(f"{Fore.CYAN}Carregando modelo NudeNet...{Style.RESET_ALL}")
        self.detector = NudeDetector()
        self.threshold = threshold
        self.debug = debug
        print(f"{Fore.GREEN}{Style.BRIGHT}Modelo carregado com sucesso!{Style.RESET_ALL}")

    def detectar_imagem(self, caminho_imagem):
        """
        Detecta nudez em uma imagem

        Args:
            caminho_imagem (str): Caminho para a imagem

        Returns:
            dict: Resultado da detecção com informações sobre nudez
        """
        if not os.path.exists(caminho_imagem):
            return {
                'erro': True,
                'mensagem': f'Arquivo não encontrado: {caminho_imagem}'
            }

        try:

            imagem = Image.open(caminho_imagem)
            imagem.verify()


            resultado = self.detector.detect(caminho_imagem)


            tem_nudez = False
            confianca_total = 0.0
            deteccoes = []
            todas_deteccoes = []
            deteccoes_candidatas = []
            deteccoes_candidatas = []

            for deteccao in resultado:
                classe = deteccao.get('class', '')
                score = deteccao.get('score', 0)


                if self.debug:
                    is_nsfw_debug = (classe in self.CLASSES_NSFW or
                                    any(keyword in classe.upper() for keyword in
                                        ['GENITALIA_EXPOSED', 'ANUS_EXPOSED', 'NIPPLE_EXPOSED',
                                         'BUTTOCK_EXPOSED', 'BREAST_EXPOSED']))

                    classes_nao_nsfw_debug = [
                        'FACE', 'FEET', 'ARMPIT', 'BELLY', 'HAND', 'FOOT', 'HEAD',
                        'ELBOW', 'KNEE', 'COVERED', 'CLOTHED', 'SHIRT', 'PANT'
                    ]
                    if any(nao_nsfw in classe.upper() for nao_nsfw in classes_nao_nsfw_debug):
                        is_nsfw_debug = False
                    if classe not in self.CLASSES_NSFW and 'EXPOSED' not in classe.upper():
                        is_nsfw_debug = False

                    todas_deteccoes.append({
                        'classe': classe,
                        'confianca': round(score * 100, 2),
                        'bbox': deteccao.get('box'),
                        'nsfw': is_nsfw_debug
                    })



                is_nsfw = (classe in self.CLASSES_NSFW or
                          any(keyword in classe.upper() for keyword in
                              ['GENITALIA_EXPOSED', 'ANUS_EXPOSED', 'NIPPLE_EXPOSED',
                               'BUTTOCK_EXPOSED', 'BREAST_EXPOSED']))



                classes_nao_nsfw = [
                    'FACE', 'FEET', 'ARMPIT', 'BELLY', 'HAND', 'FOOT', 'HEAD',
                    'ELBOW', 'KNEE', 'COVERED', 'CLOTHED', 'SHIRT', 'PANT'
                ]
                if any(nao_nsfw in classe.upper() for nao_nsfw in classes_nao_nsfw):
                    is_nsfw = False


                if classe not in self.CLASSES_NSFW:

                    if 'EXPOSED' not in classe.upper():
                        is_nsfw = False


                threshold_ajustado = self.threshold
                is_critica = (classe in self.CLASSES_CRITICAS or
                             any(keyword in classe.upper() for keyword in
                                 ['GENITALIA_EXPOSED', 'ANUS_EXPOSED']))

                if is_critica:

                    threshold_ajustado = self.threshold * 0.6

                if is_nsfw and score >= threshold_ajustado:

                    bbox = deteccao.get('box') or deteccao.get('bbox') or deteccao.get('bounding_box')
                    deteccoes_candidatas.append({
                        'classe': classe,
                        'confianca': round(score * 100, 2),
                        'confianca_raw': score,
                        'bbox': bbox,
                        'is_critica': is_critica
                    })


            deteccoes_candidatas.sort(key=lambda x: (
                not x['is_critica'],
                -x['confianca_raw']
            ))


            for det in deteccoes_candidatas:
                deteccoes.append({
                    'classe': det['classe'],
                    'confianca': det['confianca'],
                    'bbox': det['bbox']
                })
                tem_nudez = True
                confianca_total = max(confianca_total, det['confianca_raw'])

            resultado_final = {
                'erro': False,
                'tem_nudez': tem_nudez,
                'confianca': round(confianca_total * 100, 2),
                'deteccoes': deteccoes,
                'total_deteccoes': len(deteccoes),
                'caminho': caminho_imagem,
                'threshold_usado': self.threshold
            }


            if self.debug:
                resultado_final['todas_deteccoes'] = todas_deteccoes
                resultado_final['total_deteccoes_brutas'] = len(resultado)
                resultado_final['debug'] = True

            return resultado_final

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

    def processar_video(self, caminho_video, intervalo_segundos=1.0, pasta_frames=None, aplicar_blur_frames=True, pasta_saida_frames=None):
        """
        Extrai frames de um vídeo e detecta nudez em cada frame

        Args:
            caminho_video (str): Caminho para o vídeo
            intervalo_segundos (float): Intervalo entre frames extraídos (padrão: 1.0 segundo)
            pasta_frames (str): Pasta temporária para frames (None = cria pasta temporária)
            aplicar_blur_frames (bool): Se True, aplica blur nos frames com NSFW e salva
            pasta_saida_frames (str): Pasta para salvar frames editados (None = mesma pasta do vídeo)

        Returns:
            dict: Resultado com timestamps onde há nudez detectada e frames editados
        """
        if not os.path.exists(caminho_video):
            return {
                'erro': True,
                'mensagem': f'Video nao encontrado: {caminho_video}'
            }


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


        pasta_temp = None
        if pasta_frames is None:
            pasta_temp = tempfile.mkdtemp(prefix='nudez_frames_')
            pasta_frames = pasta_temp
        else:
            os.makedirs(pasta_frames, exist_ok=True)

        try:

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


            frames = sorted([f for f in os.listdir(pasta_frames) if f.startswith('frame_') and f.endswith('.jpg')])
            total_frames = len(frames)

            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {total_frames} frames extraidos")
            print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Processando frames para deteccao de nudez...")


            pasta_frames_editados = None
            if aplicar_blur_frames:
                if pasta_saida_frames is None:

                    video_dir = os.path.dirname(os.path.abspath(caminho_video))
                    video_nome = Path(caminho_video).stem
                    pasta_frames_editados = os.path.join(video_dir, f"{video_nome}_frames_editados")
                else:
                    pasta_frames_editados = pasta_saida_frames
                os.makedirs(pasta_frames_editados, exist_ok=True)
                print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Frames editados serao salvos em: {pasta_frames_editados}")


            timestamps_nsfw = []
            frames_processados = 0
            frames_editados = 0

            for i, frame_nome in enumerate(frames):
                caminho_frame = os.path.join(pasta_frames, frame_nome)




                timestamp = i * intervalo_segundos


                resultado = self.detectar_imagem(caminho_frame)

                if resultado.get('tem_nudez') and not resultado.get('erro'):

                    caminho_frame_editado = None
                    if aplicar_blur_frames:
                        resultado_blur = self.aplicar_blur(
                            caminho_frame,
                            resultado,
                            intensidade_blur=75,
                            pasta_saida=pasta_frames_editados,
                            margem_percentual=40
                        )
                        if resultado_blur.get('aplicado'):
                            caminho_frame_editado = resultado_blur['caminho_saida']
                            frames_editados += 1

                    timestamps_nsfw.append({
                        'timestamp': timestamp,
                        'tempo_formatado': self._formatar_tempo(timestamp),
                        'confianca': resultado['confianca'],
                        'total_deteccoes': resultado['total_deteccoes'],
                        'deteccoes': resultado['deteccoes'],
                        'frame': frame_nome,
                        'frame_editado': os.path.basename(caminho_frame_editado) if caminho_frame_editado else None,
                        'caminho_frame_editado': caminho_frame_editado
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
                'pasta_frames': pasta_frames
            }

            if aplicar_blur_frames:
                resultado_final['frames_editados'] = frames_editados
                resultado_final['pasta_frames_editados'] = pasta_frames_editados

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

    def _formatar_tempo(self, segundos):
        """Formata segundos em formato HH:MM:SS"""
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segs = int(segundos % 60)
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"

    def aplicar_blur(self, caminho_imagem, resultado_deteccao, intensidade_blur=75, pasta_saida=None, margem_percentual=40):
        """
        Aplica blur nas áreas onde foi detectado conteúdo NSFW

        Args:
            caminho_imagem (str): Caminho para a imagem original
            resultado_deteccao (dict): Resultado da detecção
            intensidade_blur (int): Intensidade do blur (deve ser ímpar, padrão: 75)
            pasta_saida (str): Pasta para salvar a imagem processada (None = mesma pasta)
            margem_percentual (float): Margem percentual para expandir o blur (padrão: 40%)

        Returns:
            dict: Resultado com caminho da imagem processada
        """
        if resultado_deteccao.get('erro') or not resultado_deteccao.get('tem_nudez'):
            return {
                'erro': False,
                'aplicado': False,
                'mensagem': 'Nenhum conteúdo NSFW detectado, blur não aplicado'
            }

        try:

            if intensidade_blur % 2 == 0:
                intensidade_blur += 1


            imagem = cv2.imread(caminho_imagem)
            if imagem is None:
                return {
                    'erro': True,
                    'mensagem': 'Erro ao carregar imagem com OpenCV'
                }

            altura, largura = imagem.shape[:2]
            areas_processadas = 0


            for deteccao in resultado_deteccao['deteccoes']:

                bbox = deteccao.get('bbox') or deteccao.get('box')

                if bbox and len(bbox) >= 4:
                    try:


                        bbox_values = [float(v) for v in bbox[:4]]








                        diff_x = abs(bbox_values[2] - bbox_values[0])
                        diff_y = abs(bbox_values[3] - bbox_values[1])



                        if diff_x < 10 and diff_y < 10:

                            x, y, w, h = bbox_values
                            x1, y1 = int(x), int(y)
                            x2, y2 = int(x + w), int(y + h)
                        elif bbox_values[2] > bbox_values[0] and bbox_values[3] > bbox_values[1]:

                            x1, y1, x2, y2 = [int(v) for v in bbox_values]
                        else:

                            x, y, w, h = bbox_values
                            x1, y1 = int(x), int(y)
                            x2, y2 = int(x + w), int(y + h)


                        bbox_largura = x2 - x1
                        bbox_altura = y2 - y1



                        margem_x = bbox_largura * (margem_percentual / 100.0)
                        margem_y = bbox_altura * (margem_percentual / 100.0)


                        margem_minima = 30
                        margem_x = max(margem_x, margem_minima)
                        margem_y = max(margem_y, margem_minima)


                        x1_expandido = max(0, int(x1 - margem_x))
                        y1_expandido = max(0, int(y1 - margem_y))
                        x2_expandido = min(largura, int(x2 + margem_x))
                        y2_expandido = min(altura, int(y2 + margem_y))


                        x1_final = max(0, x1_expandido)
                        y1_final = max(0, y1_expandido)
                        x2_final = min(largura, x2_expandido)
                        y2_final = min(altura, y2_expandido)


                        if x2_final > x1_final and y2_final > y1_final:

                            regiao = imagem[y1_final:y2_final, x1_final:x2_final].copy()


                            regiao_largura = x2_final - x1_final
                            regiao_altura = y2_final - y1_final



                            blur_base = max(25, int(min(regiao_largura, regiao_altura) * 0.4))
                            blur_ajustado = min(intensidade_blur, blur_base)
                            if blur_ajustado % 2 == 0:
                                blur_ajustado = max(1, blur_ajustado - 1)



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


                            imagem[y1_final:y2_final, x1_final:x2_final] = regiao_blur
                            areas_processadas += 1

                    except (ValueError, TypeError, IndexError) as e:

                        print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Erro ao processar bbox {bbox}: {e}")
                        continue
                else:

                    if areas_processadas == 0:
                        print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} Nenhum bbox valido encontrado, aplicando blur suave em toda a imagem")
                        imagem = cv2.GaussianBlur(imagem, (intensidade_blur, intensidade_blur), 0)
                        areas_processadas = 1


            if pasta_saida:
                os.makedirs(pasta_saida, exist_ok=True)
                nome_arquivo = os.path.basename(caminho_imagem)
                caminho_saida = os.path.join(pasta_saida, f"blur_{nome_arquivo}")
            else:

                diretorio = os.path.dirname(caminho_imagem)
                nome_arquivo = os.path.basename(caminho_imagem)
                caminho_saida = os.path.join(diretorio, f"blur_{nome_arquivo}")


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


def imprimir_resultado(resultado, resultado_blur=None):
    """Imprime o resultado da detecção de forma formatada com cores"""
    if resultado.get('erro'):
        print(f"{Fore.RED}{Style.BRIGHT}[ERRO]{Style.RESET_ALL} {resultado['mensagem']}")
        return

    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{Style.BRIGHT}Imagem:{Style.RESET_ALL} {Fore.YELLOW}{os.path.basename(resultado['caminho'])}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


    if resultado.get('debug'):
        print(f"{Fore.MAGENTA}{Style.BRIGHT}[DEBUG]{Style.RESET_ALL} Modo Debug Ativado")
        print(f"{Fore.CYAN}Threshold usado:{Style.RESET_ALL} {Fore.WHITE}{resultado.get('threshold_usado', 'N/A')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total de detecções brutas:{Style.RESET_ALL} {Fore.WHITE}{resultado.get('total_deteccoes_brutas', 0)}{Style.RESET_ALL}")

        if resultado.get('todas_deteccoes'):
            print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Todas as detecções (brutas):{Style.RESET_ALL}")
            for i, det in enumerate(resultado['todas_deteccoes'], 1):
                if det['nsfw']:
                    status = f"{Fore.RED}[NSFW]{Style.RESET_ALL}"
                else:
                    status = f"{Fore.BLUE}[INFO]{Style.RESET_ALL}"
                print(f"  {Fore.WHITE}{i}.{Style.RESET_ALL} {status} {Fore.YELLOW}{det['classe']}{Style.RESET_ALL}: {Fore.GREEN}{det['confianca']}%{Style.RESET_ALL}")
            print()

    if resultado['tem_nudez']:
        print(f"{Fore.RED}{Back.RED}{Style.BRIGHT} CONTEUDO NSFW DETECTADO! {Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}Confianca maxima:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{resultado['confianca']}%{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}Total de deteccoes NSFW:{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}{resultado['total_deteccoes']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Threshold usado:{Style.RESET_ALL} {Fore.WHITE}{resultado.get('threshold_usado', 'N/A')}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Detalhes das deteccoes NSFW:{Style.RESET_ALL}")
        for i, det in enumerate(resultado['deteccoes'], 1):
            print(f"  {Fore.WHITE}{i}.{Style.RESET_ALL} {Fore.RED}{det['classe']}{Style.RESET_ALL}: {Fore.YELLOW}{det['confianca']}%{Style.RESET_ALL}")


        if resultado_blur:
            if resultado_blur.get('aplicado'):
                print(f"\n{Fore.GREEN}{Style.BRIGHT}[SUCESSO]{Style.RESET_ALL} Blur aplicado com sucesso!")
                print(f"{Fore.CYAN}Imagem salva em:{Style.RESET_ALL} {Fore.WHITE}{resultado_blur['caminho_saida']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Areas com blur:{Style.RESET_ALL} {Fore.GREEN}{resultado_blur['total_areas_blur']}{Style.RESET_ALL}")
                if resultado_blur.get('margem_usada'):
                    print(f"{Fore.CYAN}Margem de expansao:{Style.RESET_ALL} {Fore.WHITE}{resultado_blur['margem_usada']}%{Style.RESET_ALL}")
            elif resultado_blur.get('erro'):
                print(f"\n{Fore.RED}{Style.BRIGHT}[ERRO]{Style.RESET_ALL} Erro ao aplicar blur: {resultado_blur['mensagem']}")
    else:
        print(f"{Fore.GREEN}{Style.BRIGHT}[SEGURO]{Style.RESET_ALL} Nenhum conteudo NSFW detectado")
        print(f"{Fore.CYAN}Threshold usado:{Style.RESET_ALL} {Fore.WHITE}{resultado.get('threshold_usado', 'N/A')}{Style.RESET_ALL}")
        if resultado.get('total_deteccoes_brutas', 0) > 0:
            print(f"{Fore.BLUE}Total de deteccoes brutas:{Style.RESET_ALL} {Fore.WHITE}{resultado['total_deteccoes_brutas']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Dica:{Style.RESET_ALL} Use --debug para ver todas as deteccoes")
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

    if resultado_video['total_cenas_nsfw'] > 0:
        print(f"\n{Fore.RED}{Back.RED}{Style.BRIGHT} CONTEUDO NSFW DETECTADO! {Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}Total de cenas com NSFW:{Style.RESET_ALL} {Fore.RED}{resultado_video['total_cenas_nsfw']}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Timestamps com conteudo NSFW:{Style.RESET_ALL}\n")

        for i, cena in enumerate(resultado_video['timestamps_nsfw'], 1):
            print(f"{Fore.WHITE}{i}.{Style.RESET_ALL} {Fore.RED}{Style.BRIGHT}Timestamp:{Style.RESET_ALL} {Fore.YELLOW}{cena['tempo_formatado']}{Style.RESET_ALL} ({cena['timestamp']:.2f}s)")
            print(f"   {Fore.CYAN}Confianca:{Style.RESET_ALL} {Fore.RED}{cena['confianca']}%{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}Deteccoes:{Style.RESET_ALL} {Fore.RED}{cena['total_deteccoes']}{Style.RESET_ALL}")
            if cena.get('frame_editado'):
                print(f"   {Fore.GREEN}Frame editado:{Style.RESET_ALL} {Fore.WHITE}{cena['frame_editado']}{Style.RESET_ALL}")
            print(f"   {Fore.CYAN}Classes detectadas:{Style.RESET_ALL}")
            for det in cena['deteccoes']:
                print(f"      - {Fore.YELLOW}{det['classe']}{Style.RESET_ALL}: {Fore.GREEN}{det['confianca']}%{Style.RESET_ALL}")
            print()
    else:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}[SEGURO]{Style.RESET_ALL} Nenhum conteudo NSFW detectado no video")
        print(f"{Fore.GREEN}O video parece ser seguro.{Style.RESET_ALL}")

    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


def main():
    """Função principal"""
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}  DETECTOR DE NUDEZ - NudeNet{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")


    aplicar_blur = False
    intensidade_blur = 75
    pasta_saida = None
    caminho = None
    threshold = 0.20
    debug = False
    margem_blur = 40
    processar_video = False
    intervalo_video = 1.0

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
            print("  --threshold, -t NUM     Threshold de confiança (0.0-1.0, padrão: 0.3)")
            print("  --debug, -d             Mostra todas as detecções (modo debug)")
            print("  --video, -v             Processa um vídeo (extrai frames e detecta nudez)")
            print("  --intervalo NUM         Intervalo entre frames em segundos (padrão: 1.0)")
            print("  --help, -h              Mostra esta ajuda")
            print("\nExemplos:")
            print(f"  python3 {sys.argv[0]} foto.jpg")
            print(f"  python3 {sys.argv[0]} --blur foto.jpg")
            print(f"  python3 {sys.argv[0]} --blur -i 95 foto.jpg  # Blur muito intenso")
            print(f"  python3 {sys.argv[0]} --threshold 0.2 foto.jpg  # Mais sensível")
            print(f"  python3 {sys.argv[0]} --debug foto.jpg  # Ver todas as detecções")
            print(f"  python3 {sys.argv[0]} --blur -o ./saida/ ./pasta_imagens/")
            print(f"  python3 {sys.argv[0]} --video video.mp4  # Processa video")
            print(f"  python3 {sys.argv[0]} --video --intervalo 2.0 video.mp4  # Frame a cada 2 segundos")
            sys.exit(0)
        else:
            if caminho is None:
                caminho = arg
            i += 1


    detector = DetectorNudez(threshold=threshold, debug=debug)

    if caminho is None:
        print(f"\n{Fore.RED}[ERRO]{Style.RESET_ALL} Caminho da imagem, pasta ou video nao especificado")
        print(f"{Fore.YELLOW}Use --help para ver as opcoes disponiveis{Style.RESET_ALL}")
        sys.exit(1)


    if processar_video:
        if not os.path.isfile(caminho):
            print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} Arquivo de video nao encontrado: {caminho}")
            sys.exit(1)

        resultado_video = detector.processar_video(caminho, intervalo_video)
        imprimir_resultado_video(resultado_video)
        sys.exit(0)


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

        total_nsfw = sum(1 for r in resultados if r.get('tem_nudez', False))
        print(f"{Fore.RED}{Style.BRIGHT}Imagens com NSFW:{Style.RESET_ALL} {Fore.RED}{total_nsfw}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{Style.BRIGHT}Imagens seguras:{Style.RESET_ALL} {Fore.GREEN}{len(resultados) - total_nsfw}{Style.RESET_ALL}")

        if aplicar_blur:
            print(f"\n{Fore.CYAN}[PROCESSANDO]{Style.RESET_ALL} Aplicando blur nas imagens detectadas...")
            total_blur = 0
            for resultado in resultados:
                if resultado.get('tem_nudez'):
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

