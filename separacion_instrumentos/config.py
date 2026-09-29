import os
import json

CONFIG_FILE = "app_config.json"

def check_cuda_support():
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False

class ConfigManager:
    def __init__(self):
        self.config = {
            "ffmpeg_path": self._find_default_ffmpeg(),
            "device": "cuda" if check_cuda_support() else "cpu",
            "model": "htdemucs", # "htdemucs" (4 stems) or "htdemucs_6s" (6 stems)
            "output_dir": os.path.abspath("monosync")
        }
        self.load_config()

    def _find_default_ffmpeg(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_ffmpeg = os.path.join(script_dir, "ffmpeg.exe")
        if os.path.isfile(local_ffmpeg):
            return script_dir
        
        cwd_ffmpeg = os.path.join(os.getcwd(), "ffmpeg.exe")
        if os.path.isfile(cwd_ffmpeg):
            return os.getcwd()
            
        return script_dir

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                print(f"Error cargando configuracion: {e}")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isfile(os.path.join(script_dir, "ffmpeg.exe")):
            self.config["ffmpeg_path"] = script_dir

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error guardando configuracion: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
