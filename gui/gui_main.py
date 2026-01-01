#!/usr/bin/env python3
"""
GUI Principal - Detector de Nudez v2.0
Interface gráfica moderna usando CustomTkinter
"""

import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import threading
from pathlib import Path
import sys
import os

# Adiciona src ao path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Muda para diretório do projeto
os.chdir(str(project_root))

from detector_nudez_v2 import DetectorNudez

# Configuração do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DetectorApp(ctk.CTk):
    """Aplicação principal GUI"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🔍 Detector de Nudez v2.0 - Análise de Vídeo")
        self.geometry("1000x800")
        self.minsize(900, 700)
        
        # Variáveis
        self.selected_file = None
        self.processing = False
        self.detector = None
        self.detector_ready = False
        
        # Cria interface PRIMEIRO (antes de inicializar detector)
        self.create_widgets()
        
        # Centraliza janela
        self.center_window()
        
        # Inicializa detector DEPOIS (pode ser lento, então fazemos async)
        # Agora os widgets já existem, então podemos usar self.log()
        self._init_detector_async()
    
    def center_window(self):
        """Centraliza a janela na tela"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _init_detector_async(self):
        """Inicializa detector em thread separada"""
        def init_worker():
            try:
                self.detector = DetectorNudez(threshold=0.20, debug=False)  # Máxima sensibilidade
                self.after(0, self._on_detector_ready)
            except Exception as e:
                self.after(0, lambda: self.log_error(f"Erro ao inicializar detector: {str(e)}"))
        
        thread = threading.Thread(target=init_worker, daemon=True)
        thread.start()
        self.log("Inicializando detector...")
    
    def _on_detector_ready(self):
        """Callback quando detector está pronto"""
        self.detector_ready = True
        self.log("✓ Detector inicializado com sucesso!")
        self.log("Sistema iniciado. Aguardando seleção de arquivo...")
        self.select_btn.configure(state="normal")
    
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        
        # Título
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(20, 10))
        
        title = ctk.CTkLabel(
            title_frame,
            text="🔍 Detector de Nudez",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Análise de Vídeo - Descrições com Timestamps",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        
        subtitle = ctk.CTkLabel(
        title_frame,
        text="Criado por @_.guusta",
        font=ctk.CTkFont(size=14),
        text_color="red"
        )
        subtitle.pack()
        
        # Frame principal (scrollable)
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Seleção de arquivo
        self.create_file_selection(main_frame)
        
        # Configurações
        self.create_config_section(main_frame)
        
        # Botões de ação
        self.create_action_buttons(main_frame)
        
        # Progresso
        self.create_progress_section(main_frame)
        
        # Resultado
        self.create_result_section(main_frame)
        
        # Logs
        self.create_logs_section(main_frame)
    
    def create_file_selection(self, parent):
        """Cria seção de seleção de arquivo"""
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", pady=10, padx=10)
        
        label = ctk.CTkLabel(file_frame, text="📹 Vídeo:", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(side="left", padx=10, pady=10)
        
        self.file_label = ctk.CTkLabel(
            file_frame,
            text="Nenhum vídeo selecionado",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.file_label.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        self.select_btn = ctk.CTkButton(
            file_frame,
            text="Selecionar Vídeo",
            command=self.select_file,
            state="disabled"  # Desabilitado até detector estar pronto
        )
        self.select_btn.pack(side="right", padx=10, pady=10)
    
    def create_config_section(self, parent):
        """Cria seção de configurações (simplificada)"""
        config_frame = ctk.CTkFrame(parent)
        config_frame.pack(fill="x", pady=10, padx=10)
        
        # Título
        config_title = ctk.CTkLabel(
            config_frame,
            text="⚙️ Configurações",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Threshold
        threshold_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        threshold_frame.pack(fill="x", padx=10, pady=5)
        
        threshold_label = ctk.CTkLabel(threshold_frame, text="Threshold:", width=120)
        threshold_label.pack(side="left", padx=5)
        
        self.threshold_slider = ctk.CTkSlider(
            threshold_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            command=self._on_threshold_change
        )
        self.threshold_slider.set(0.20)  # Threshold reduzido para máxima sensibilidade
        self.threshold_slider.pack(side="left", padx=5, fill="x", expand=True)
        
        self.threshold_value = ctk.CTkLabel(threshold_frame, text="0.20", width=50)
        self.threshold_value.pack(side="left", padx=5)
        
        # Intervalo entre frames
        interval_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=10, pady=5)
        
        interval_label = ctk.CTkLabel(interval_frame, text="Intervalo (seg):", width=120)
        interval_label.pack(side="left", padx=5)
        
        self.interval_slider = ctk.CTkSlider(
            interval_frame,
            from_=0.5,
            to=5.0,
            number_of_steps=45,
            command=self._on_interval_change
        )
        self.interval_slider.set(0.5)  # Intervalo menor = mais frames analisados = melhor detecção
        self.interval_slider.pack(side="left", padx=5, fill="x", expand=True)
        
        self.interval_value = ctk.CTkLabel(interval_frame, text="0.5", width=50)
        self.interval_value.pack(side="left", padx=5)
    
    def create_action_buttons(self, parent):
        """Cria botões de ação"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=10, padx=10)
        
        self.process_btn = ctk.CTkButton(
            button_frame,
            text="▶ Processar",
            command=self.process_file,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            state="disabled"
        )
        self.process_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="⏹ Parar",
            command=self.stop_processing,
            font=ctk.CTkFont(size=16),
            height=40,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5, fill="x", expand=True)
    
    def create_progress_section(self, parent):
        """Cria seção de progresso"""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", pady=10, padx=10)
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progresso:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        progress_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Aguardando...",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.progress_label.pack(anchor="w", padx=10, pady=(0, 10))
    
    def create_logs_section(self, parent):
        """Cria seção de logs"""
        logs_frame = ctk.CTkFrame(parent)
        logs_frame.pack(fill="both", expand=True, pady=10, padx=10)
        
        logs_title = ctk.CTkLabel(
            logs_frame,
            text="📋 Logs",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        logs_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(logs_frame, height=150)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Mensagem inicial será adicionada quando detector estiver pronto
    
    def create_result_section(self, parent):
        """Cria seção de resultados"""
        result_frame = ctk.CTkFrame(parent)
        result_frame.pack(fill="both", expand=True, pady=10, padx=10)
        
        result_title = ctk.CTkLabel(
            result_frame,
            text="📊 Resultado",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        result_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.result_label = ctk.CTkLabel(
            result_frame,
            text="Nenhum resultado ainda",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.result_label.pack(anchor="w", padx=10, pady=(0, 5))
        
        # Área de texto para timestamps
        self.result_text = ctk.CTkTextbox(result_frame, height=200, font=ctk.CTkFont(size=11))
        self.result_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        self.save_btn = ctk.CTkButton(
            result_frame,
            text="💾 Salvar Resultado (JSON)",
            command=self.save_result,
            state="disabled"
        )
        self.save_btn.pack(anchor="w", padx=10, pady=(0, 10))
    
    def _on_threshold_change(self, value):
        """Callback quando threshold muda"""
        self.threshold_value.configure(text=f"{value:.2f}")
    
    def _on_interval_change(self, value):
        """Callback quando intervalo muda"""
        self.interval_value.configure(text=f"{value:.1f}")
    
    def select_file(self):
        """Abre diálogo para selecionar vídeo"""
        filename = filedialog.askopenfilename(
            title="Selecionar Vídeo",
            filetypes=[
                ("Vídeos", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("Todos os arquivos", "*.*")
            ]
        )
        
        if filename:
            self.selected_file = filename
            file_name = Path(filename).name
            self.file_label.configure(text=file_name, text_color="white")
            self.log(f"✓ Vídeo selecionado: {file_name}")
            self.process_btn.configure(state="normal")
            self.result_label.configure(text="Vídeo selecionado. Pronto para processar.", text_color="gray")
            self.save_btn.configure(state="disabled")
            # Limpa resultados anteriores
            self.result_text.delete("1.0", "end")
    
    def process_file(self):
        """Inicia processamento do arquivo"""
        if not self.detector_ready or not self.detector:
            messagebox.showerror("Erro", "Detector ainda não está pronto. Aguarde alguns segundos.")
            return
        
        if not self.selected_file:
            messagebox.showwarning("Aviso", "Selecione um arquivo primeiro!")
            return
        
        if self.processing:
            messagebox.showinfo("Info", "Já está processando um arquivo!")
            return
        
        # Atualiza UI
        self.processing = True
        self.process_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando processamento...")
        self.result_label.configure(text="Processando...", text_color="orange")
        self.save_btn.configure(state="disabled")
        
        # Atualiza configurações do detector
        self.detector.threshold = self.threshold_slider.get()
        
        # Processa em thread separada
        thread = threading.Thread(target=self._process_worker, daemon=True)
        thread.start()
    
    def _process_worker(self):
        """Worker thread para processamento (apenas vídeos)"""
        try:
            file_path = Path(self.selected_file)
            file_ext = file_path.suffix.lower()
            
            if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                self._process_video(file_path)
            else:
                self.after(0, lambda: self.log_error(f"Tipo de arquivo não suportado. Use vídeo (mp4, avi, mov, mkv, webm)"))
                self.after(0, self._processing_done)
        
        except Exception as e:
            self.after(0, lambda: self.log_error(f"Erro no processamento: {str(e)}"))
            self.after(0, self._processing_done)
    
    def _process_video(self, file_path):
        """Processa vídeo e retorna descrições com timestamps"""
        self.after(0, lambda: self.log("Processando vídeo..."))
        self.after(0, lambda: self.progress_label.configure(text="Analisando vídeo..."))
        self.after(0, lambda: self.progress_bar.set(0.1))
        
        intervalo = self.interval_slider.get()
        
        resultado = self.detector.obter_descricao_nudez_video(
            str(file_path),
            intervalo_segundos=intervalo
        )
        
        self.after(0, lambda: self.progress_bar.set(0.9))
        
        if resultado.get('erro'):
            self.after(0, lambda: self.log_error(f"Erro: {resultado.get('mensagem')}"))
        else:
            self.after(0, lambda: self._handle_video_result(resultado))
        
        self.after(0, lambda: self.progress_bar.set(1.0))
        self.after(0, lambda: self.progress_label.configure(text="Concluído!"))
        self.after(0, self._processing_done)
    
    def _handle_video_result(self, resultado):
        """Exibe resultado de vídeo com descrições"""
        tem_nudez = resultado.get('tem_nudez', False)
        tipo_nudez = resultado.get('tipo_nudez', 'SAFE')
        descricao_geral = resultado.get('descricao_geral', '')
        duracao = resultado.get('duracao_formatada', '')
        total_timestamps = len(resultado.get('timestamps', []))
        
        # Cores baseadas no tipo
        if tipo_nudez == 'NSFW':
            color = "red"
            icon = "🔴"
        elif tipo_nudez == 'SUGGESTIVE':
            color = "orange"
            icon = "🟠"
        else:
            color = "green"
            icon = "🟢"
        
        # Texto resumido
        if tem_nudez:
            resultado_text = f"{icon} {tipo_nudez} | {total_timestamps} timestamp(s) | Duração: {duracao}"
        else:
            resultado_text = f"{icon} {tipo_nudez} | Nenhuma detecção | Duração: {duracao}"
        
        self.result_label.configure(text=resultado_text, text_color=color)
        
        # Log detalhado
        self.log(f"✓ Análise concluída!")
        self.log(f"  Tipo: {tipo_nudez}")
        self.log(f"  Duração: {duracao} ({resultado.get('duracao_total', 0):.2f}s)")
        self.log(f"  Frames processados: {resultado.get('total_frames_processados', 0)}")
        self.log(f"  Timestamps com detecção: {total_timestamps}")
        
        if descricao_geral:
            self.log(f"  {descricao_geral}")
        
        # Mostrar estatísticas se disponível
        if resultado.get('resumo'):
            resumo = resultado['resumo']
            self.log(f"  NSFW: {resumo.get('total_frames_nsfw', 0)} | "
                     f"SUGGESTIVE: {resumo.get('total_frames_suggestive', 0)} | "
                     f"SAFE: {resumo.get('total_frames_safe', 0)}")
        
        self.result_data = resultado
        self.save_btn.configure(state="normal")
        
        # Exibir timestamps na área de resultados
        self._display_timestamps(resultado.get('timestamps', []))
    
    def _display_timestamps(self, timestamps):
        """Exibe timestamps na área de resultados"""
        # Limpar área de resultados
        self.result_text.delete("1.0", "end")
        
        if not timestamps:
            self.result_text.insert("1.0", "Nenhum timestamp com detecção encontrado.")
            return
        
        # Exibir timestamps
        for i, ts in enumerate(timestamps, 1):
            timestamp_str = f"{ts['tempo_formatado']} ({ts['timestamp']:.1f}s)"
            tipo = ts.get('tipo_nudez', 'UNKNOWN')
            descricao = ts.get('descricao', '')
            
            # Emoji baseado no tipo
            if tipo == 'NSFW':
                emoji = "🔴"
            elif tipo == 'SUGGESTIVE':
                emoji = "🟠"
            else:
                emoji = "🟢"
            
            self.result_text.insert("end", f"{i}. {emoji} {timestamp_str} [{tipo}]\n")
            self.result_text.insert("end", f"   {descricao}\n\n")
        
        # Scroll para o topo
        self.result_text.see("1.0")
    
    def stop_processing(self):
        """Para processamento (placeholder - implementação real seria mais complexa)"""
        self.log("⚠ Parar processamento solicitado (implementação futura)")
        # Nota: Parar processamento em andamento é complexo e requer
        # implementação de flags compartilhadas ou killing da thread
        # Por agora, apenas desabilita o botão
        messagebox.showinfo("Info", "Para parar completamente, feche e reabra a aplicação")
    
    def save_result(self):
        """Salva resultado"""
        if not hasattr(self, 'result_data'):
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Salvar resultado",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")]
        )
        
        if filename:
            import json
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.result_data, f, indent=2, ensure_ascii=False)
                self.log(f"✓ Resultado salvo em: {Path(filename).name}")
                messagebox.showinfo("Sucesso", "Resultado salvo com sucesso!")
            except Exception as e:
                self.log_error(f"Erro ao salvar: {str(e)}")
                messagebox.showerror("Erro", f"Erro ao salvar resultado: {str(e)}")
    
    def log(self, message):
        """Adiciona mensagem aos logs"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
    
    def log_error(self, message):
        """Adiciona erro aos logs"""
        self.log_text.insert("end", f"❌ {message}\n")
        self.log_text.see("end")
    
    def _processing_done(self):
        """Callback quando processamento termina"""
        self.processing = False
        self.process_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")


def main():
    """Função principal"""
    app = DetectorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

