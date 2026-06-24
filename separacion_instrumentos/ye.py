import customtkinter as ctk
import pygame
import os
import threading
import subprocess
import sys
import torch
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StemPlayerIsaac6S(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stem Player AI - 6 Stems Edition")
        self.geometry("800x800")

        pygame.mixer.init()
        # Nombres para el modelo de 6 pistas
        self.nombres_6s = ["VOCALS", "DRUMS", "BASS", "PIANO", "GUITAR", "OTHER"]
        self.nombres_4s = ["VOCALS", "DRUMS", "BASS", "OTHER"]

        self.canales_audio = []
        self.sliders = []
        self.reproduciendo = False
        self.ffmpeg_path = ""

        self.crear_interfaz()

    def crear_interfaz(self):
        self.label = ctk.CTkLabel(self, text="STEM PLAYER AI 6-CHANNELS", font=("Helvetica", 24, "bold"),
                                  text_color="#FF4500")
        self.label.pack(pady=20)

        # Panel Configuración
        self.frame_config = ctk.CTkFrame(self)
        self.frame_config.pack(pady=10, padx=20, fill="x")

        self.btn_config = ctk.CTkButton(self.frame_config, text="1. Buscar ffmpeg.exe", command=self.seleccionar_ffmpeg)
        self.btn_config.pack(pady=10, padx=10)

        # SELECTOR DE MODELO (4 o 6 pistas)
        ctk.CTkLabel(self.frame_config, text="2. Seleccionar Cantidad de Sonidos:",
                     font=("Helvetica", 12, "bold")).pack()
        self.model_var = ctk.StringVar(value="htdemucs")  # Por defecto 4
        self.model_menu = ctk.CTkSegmentedButton(self.frame_config, values=["htdemucs", "htdemucs_6s"],
                                                 variable=self.model_var)
        self.model_menu.pack(pady=10)

        # Selector de Hardware
        self.device_var = ctk.StringVar(value="cuda" if torch.cuda.is_available() else "cpu")
        self.device_menu = ctk.CTkSegmentedButton(self.frame_config, values=["cpu", "cuda"], variable=self.device_var)
        self.device_menu.pack(pady=5)

        self.btn_importar = ctk.CTkButton(self, text="SELECCIONAR Y SEPARAR", height=40, command=self.iniciar_proceso)
        self.btn_importar.pack(pady=20)

        self.progress = ctk.CTkProgressBar(self, width=500)
        self.progress.set(0)
        self.progress.pack(pady=10)

        # Contenedor para Sliders (Se limpia y regenera según el modelo)
        self.frame_mixer = ctk.CTkFrame(self, fg_color="#1A1A1A", corner_radius=15)
        self.frame_mixer.pack(padx=20, pady=20, fill="both", expand=True)

        self.generar_sliders(4)  # Iniciar con 4 por defecto

        self.btn_play = ctk.CTkButton(self, text="PLAY", state="disabled", height=50, command=self.toggle_playback)
        self.btn_play.pack(pady=20)

    def generar_sliders(self, cantidad):
        # Limpiar sliders viejos
        for widget in self.frame_mixer.winfo_children():
            widget.destroy()
        self.sliders = []

        nombres = self.nombres_6s if cantidad == 6 else self.nombres_4s
        for i, nombre in enumerate(nombres):
            frame_col = ctk.CTkFrame(self.frame_mixer, fg_color="transparent")
            frame_col.pack(side="left", expand=True, fill="y", padx=5)
            s = ctk.CTkSlider(frame_col, orientation="vertical", from_=1.0, to=0.0,
                              command=lambda v, idx=i: self.set_vol(v, idx))
            s.set(0.7)
            s.pack(pady=10, expand=True)
            self.sliders.append(s)
            ctk.CTkLabel(frame_col, text=nombre, font=("Helvetica", 10, "bold")).pack()

    def seleccionar_ffmpeg(self):
        ruta = filedialog.askopenfilename(title="Selecciona ffmpeg.exe")
        if ruta: self.ffmpeg_path = os.path.dirname(ruta)

    def iniciar_proceso(self):
        if not self.ffmpeg_path: return messagebox.showwarning("Error", "Configura FFmpeg")
        archivo = filedialog.askopenfilename()
        if archivo:
            modelo = self.model_var.get()
            self.generar_sliders(6 if "6s" in modelo else 4)
            self.progress.start()
            threading.Thread(target=self.separar_ia, args=(archivo, modelo), daemon=True).start()

    def separar_ia(self, ruta_archivo, modelo):
        try:
            env = os.environ.copy()
            env["PATH"] = self.ffmpeg_path + os.pathsep + env["PATH"]
            dispositivo = self.device_var.get()

            comando = [sys.executable, "-m", "demucs.separate", "-n", modelo, "-d", dispositivo, ruta_archivo, "-o",
                       "output_test"]
            subprocess.run(comando, check=True, env=env, shell=False)

            nombre_cancion = os.path.splitext(os.path.basename(ruta_archivo))[0]
            ruta_base = os.path.join("output_test", modelo, nombre_cancion)

            stems = ["vocals.wav", "drums.wav", "bass.wav", "piano.wav", "guitar.wav",
                     "other.wav"] if "6s" in modelo else ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]

            self.canales_audio = []
            for f in stems:
                self.canales_audio.append(pygame.mixer.Sound(os.path.join(ruta_base, f)))

            self.after(0, self.exito)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def exito(self):
        self.progress.stop()
        self.progress.set(1)
        self.btn_play.configure(state="normal", fg_color="green")

    def set_vol(self, v, idx):
        if self.reproduciendo and idx < len(self.canales_audio):
            pygame.mixer.Channel(idx).set_volume(float(v))

    def toggle_playback(self):
        if not self.reproduciendo:
            for i, s in enumerate(self.canales_audio):
                pygame.mixer.Channel(i).play(s)
                pygame.mixer.Channel(i).set_volume(self.sliders[i].get())
            self.reproduciendo = True
            self.btn_play.configure(text="STOP", fg_color="red")
        else:
            pygame.mixer.stop()
            self.reproduciendo = False
            self.btn_play.configure(text="PLAY", fg_color="green")


if __name__ == "__main__":
    app = StemPlayerIsaac6S()
    app.mainloop()