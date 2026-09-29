import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from PIL import Image

from config import ConfigManager
from audio_engine import AudioEngine
from separator import DemucsSeparator
from ui_left_panel import LeftPanel
from ui_center_panel import CenterPanel
from ui_right_panel import RightPanel
from metadata_utils import get_cover_image

QSS_MACOS_DARK = """
QMainWindow {
    background-color: #0D0D0E;
}
QFrame#CardBlock {
    background-color: #1C1C1E;
    border-radius: 14px;
    border: 1px solid #2C2C2E;
}
QLabel {
    color: #F2F2F7;
    font-family: 'SF Pro Display', 'Segoe UI', sans-serif;
}
QScrollBar:vertical {
    border: none;
    background: #121214;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #3A3A3C;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #545456;
}
"""

class MonoSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MonoSync Studio - Stem Player & AI Separator (Qt Edition)")
        self.resize(1200, 840)
        self.setMinimumSize(1020, 700)

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

    def _build_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Left Panel (30% width)
        self.left_panel = LeftPanel(
            self.config_manager,
            self.audio_engine,
            self.separator
        )
        self.left_panel.song_selected.connect(self._on_song_select)
        self.left_panel.model_changed.connect(self._on_model_change)
        main_layout.addWidget(self.left_panel, stretch=3)

        # Center Panel (40% width)
        self.center_panel = CenterPanel(
            self.config_manager,
            self.audio_engine
        )
        main_layout.addWidget(self.center_panel, stretch=4)

        # Right Panel (30% width)
        self.right_panel = RightPanel(self.config_manager)
        self.right_panel.play_stems_requested.connect(self._play_stems_song)
        main_layout.addWidget(self.right_panel, stretch=3)

    def _on_model_change(self, model_name):
        stems = ["VOCALS", "DRUMS", "BASS", "PIANO", "GUITAR", "OTHER"] if "6s" in model_name else ["VOCALS", "DRUMS", "BASS", "OTHER"]
        self.center_panel.render_mixer_sliders(stems)

    def _on_song_select(self, song_meta, mode):
        song_path = song_meta["path"]
        title = song_meta["title"]
        artist = song_meta["artist"]

        cover_image = song_meta.get("cover_image")
        if cover_image is None:
            cover_image = get_cover_image(song_path)
            song_meta["cover_image"] = cover_image

        if mode == "single_preview":
            self.center_panel.load_track_info(title, artist, mode="Preview", cover_image=cover_image)
        elif mode == "single_play":
            self.audio_engine.load_single(song_path)
            self.center_panel.load_track_info(title, artist, mode="Original", cover_image=cover_image)
            self.audio_engine.play()

    def _play_stems_song(self, folder_path, song_name, stems_list):
        self.audio_engine.load_stems(folder_path, stems_list)

        meta = {"artist": "MonoSync Stems", "title": song_name, "cover_image": None}
        for file in os.listdir(folder_path):
            if file.lower().endswith((".jpg", ".png", ".jpeg")):
                try:
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

    def _on_sep_start(self, song_name, current, total):
        QTimer.singleShot(0, self.left_panel.update_queue_status)

    def _on_sep_finish(self, song_name, output_folder):
        QTimer.singleShot(0, self.left_panel.update_queue_status)
        QTimer.singleShot(0, self.right_panel.refresh_divided_songs)

    def _on_sep_queue_finish(self):
        QTimer.singleShot(0, self.left_panel.update_queue_status)
        QTimer.singleShot(0, self.right_panel.refresh_divided_songs)

    def _on_sep_error(self, song_name, err):
        QTimer.singleShot(0, self.left_panel.update_queue_status)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS_MACOS_DARK)
    window = MonoSyncApp()
    window.show()
    sys.exit(app.exec())