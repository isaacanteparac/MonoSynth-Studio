import os
import sys
import customtkinter as ctk
from config import ConfigManager
from audio_engine import AudioEngine
from separator import DemucsSeparator
from ui_left_panel import LeftPanel
from ui_center_panel import CenterPanel
from ui_right_panel import RightPanel
from metadata_utils import get_song_metadata

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MonoSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MonoSync Studio - Stem Player & AI Separator")
        self.geometry("1180x800")
        self.minsize(1000, 680)
        self.configure(fg_color="#0D0D0E")

        # Initialize Core Engines
        self.config_manager = ConfigManager()
        self.audio_engine = AudioEngine()
        self.separator = DemucsSeparator(self.config_manager)

        # Wire background separator callbacks
        self.separator.on_item_start = self._on_sep_start
        self.separator.on_item_finish = self._on_sep_finish
        self.separator.on_queue_finish = self._on_sep_queue_finish
        self.separator.on_error = self._on_sep_error

        self._build_layout()

        # Start Mini Player position tick loop
        self.center_panel.update_player_loop()

    def _build_layout(self):
        # 3-Column Layout Configuration
        self.grid_columnconfigure(0, weight=3) # Left Panel: 30%
        self.grid_columnconfigure(1, weight=4) # Center Panel: 40%
        self.grid_columnconfigure(2, weight=3) # Right Panel: 30%
        self.grid_rowconfigure(0, weight=1)

        # Left Panel (Undivided songs accordion + Conversion settings)
        self.left_panel = LeftPanel(
            self,
            self.config_manager,
            self.audio_engine,
            self.separator,
            on_song_select_callback=self._on_song_select
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)

        # Center Panel (Cover + Stem Mixer + Mini Player with Seek)
        self.center_panel = CenterPanel(
            self,
            self.config_manager,
            self.audio_engine
        )
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=8, pady=15)

        # Right Panel (Divided songs monosync folder tree)
        self.right_panel = RightPanel(
            self,
            self.config_manager,
            on_play_stems_callback=self._play_stems_song
        )
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 15), pady=15)

    def _on_song_select(self, song_meta, mode="single_play"):
        song_path = song_meta["path"]
        title = song_meta["title"]
        artist = song_meta["artist"]
        cover_image = song_meta.get("cover_image")

        if mode == "single_preview":
            # Update Cover and track info on selection
            self.center_panel.load_track_info(title, artist, mode="Preview", cover_image=cover_image)
        elif mode == "single_play":
            # Load track into audio engine and play
            self.audio_engine.load_single(song_path)
            self.center_panel.load_track_info(title, artist, mode="Original", cover_image=cover_image)
            self.audio_engine.play()
            self.center_panel.btn_play_pause.configure(text="⏸ PAUSE", fg_color="#FF9F0A")

    def _play_stems_song(self, folder_path, song_name, stems_list):
        self.audio_engine.load_stems(folder_path, stems_list)

        # Try extracting cover image from separated folder or metadata
        meta = {"artist": "MonoSync Stems", "title": song_name, "cover_image": None}
        for file in os.listdir(folder_path):
            if file.lower().endswith((".jpg", ".png", ".jpeg")):
                try:
                    from PIL import Image
                    meta["cover_image"] = Image.open(os.path.join(folder_path, file))
                    break
                except Exception:
                    pass

        self.center_panel.load_track_info(
            song_name,
            artist=meta["artist"],
            mode="Stems Remixed",
            cover_image=meta.get("cover_image"),
            stems=stems_list
        )
        self.audio_engine.play()
        self.center_panel.btn_play_pause.configure(text="⏸ PAUSE", fg_color="#FF9F0A")

    # Separator Event Callbacks
    def _on_sep_start(self, song_name, current, total):
        self.after(0, lambda: self.left_panel.update_queue_status())

    def _on_sep_finish(self, song_name, output_folder):
        self.after(0, lambda: self.left_panel.update_queue_status())
        self.after(0, lambda: self.right_panel.refresh_divided_songs())

    def _on_sep_queue_finish(self):
        self.after(0, lambda: self.left_panel.update_queue_status())
        self.after(0, lambda: self.right_panel.refresh_divided_songs())

    def _on_sep_error(self, song_name, err):
        self.after(0, lambda: self.left_panel.update_queue_status())

if __name__ == "__main__":
    app = MonoSyncApp()
    app.mainloop()