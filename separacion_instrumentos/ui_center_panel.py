import os
import io
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSlider, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage
from PIL import Image

STEM_LAYOUT_6S = [
    ("VOCALS", 0, 0), ("DRUMS", 0, 1), ("BASS", 0, 2),
    ("PIANO", 1, 0),  ("GUITAR", 1, 1), ("OTHER", 1, 2)
]

STEM_LAYOUT_4S = [
    ("VOCALS", 0, 0), ("DRUMS", 0, 1), ("BASS", 0, 2),
    ("OTHER", 1, 1)
]

class CenterPanel(QWidget):
    def __init__(self, config_manager, audio_engine):
        super().__init__()
        self.config = config_manager
        self.audio_engine = audio_engine

        self.current_stems = ["VOCALS", "DRUMS", "BASS", "PIANO", "GUITAR", "OTHER"]
        self.slider_widgets = {}
        self.mute_buttons = {}
        self.solo_buttons = {}
        self.is_user_seeking = False

        self._create_ui()

        # Wire audio finish callback & position loop timer
        self.audio_engine.on_finish_callback = self._on_playback_finished
        
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_player_loop)
        self.timer.start()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # TOP CARD BLOCK: Cover Art
        self.cover_card = QFrame()
        self.cover_card.setObjectName("CardBlock")
        cover_layout = QVBoxLayout(self.cover_card)
        cover_layout.setContentsMargins(12, 12, 12, 12)
        cover_layout.setSpacing(4)

        self.lbl_cover_art = QLabel("💿")
        self.lbl_cover_art.setAlignment(Qt.AlignCenter)
        self.lbl_cover_art.setStyleSheet("font-size: 56px; background-color: #121214; border-radius: 12px;")
        cover_layout.addWidget(self.lbl_cover_art, stretch=1)

        self.lbl_cover_artist = QLabel("")
        self.lbl_cover_artist.setAlignment(Qt.AlignCenter)
        self.lbl_cover_artist.setStyleSheet("font-size: 11px; color: #8E8E93;")
        cover_layout.addWidget(self.lbl_cover_artist)

        self.lbl_cover_title = QLabel("Selecciona una canción")
        self.lbl_cover_title.setAlignment(Qt.AlignCenter)
        self.lbl_cover_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #F2F2F7;")
        cover_layout.addWidget(self.lbl_cover_title)

        main_layout.addWidget(self.cover_card, stretch=2)

        # MIDDLE CARD BLOCK: Stem Mixer (Grid 2 rows x 3 cols)
        self.mixer_card = QFrame()
        self.mixer_card.setObjectName("CardBlock")
        mixer_layout = QVBoxLayout(self.mixer_card)
        mixer_layout.setContentsMargins(12, 10, 12, 10)
        mixer_layout.setSpacing(6)

        lbl_mix_title = QLabel("Mezclador de Instrumentos")
        lbl_mix_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #F2F2F7;")
        mixer_layout.addWidget(lbl_mix_title)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(6)
        mixer_layout.addWidget(self.grid_container, stretch=1)

        self.render_mixer_sliders(self.current_stems)

        main_layout.addWidget(self.mixer_card, stretch=3)

        # BOTTOM CARD BLOCK: Mini Player
        self.player_card = QFrame()
        self.player_card.setObjectName("CardBlock")
        player_layout = QVBoxLayout(self.player_card)
        player_layout.setContentsMargins(12, 10, 12, 10)
        player_layout.setSpacing(6)

        info_layout = QHBoxLayout()
        self.lbl_now_playing = QLabel("Sin reproducción")
        self.lbl_now_playing.setStyleSheet("font-size: 12px; font-weight: bold; color: #F2F2F7;")
        info_layout.addWidget(self.lbl_now_playing)
        info_layout.addStretch()

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("font-size: 11px; color: #8E8E93;")
        info_layout.addWidget(self.lbl_time)
        player_layout.addLayout(info_layout)

        # Seek Bar Slider
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setValue(0)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #2C2C2E; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #30D158; border-radius: 2px; }
            QSlider::handle:horizontal { background: #30D158; width: 12px; margin-top: -4px; margin-bottom: -4px; border-radius: 6px; }
        """)
        self.seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self.seek_slider.sliderReleased.connect(self._on_seek_released)
        player_layout.addWidget(self.seek_slider)

        # Control Row
        ctrl_layout = QHBoxLayout()

        self.btn_play = QPushButton("▶ PLAY")
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.setStyleSheet("background-color: #30D158; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        self.btn_play.clicked.connect(self._toggle_play_pause)
        ctrl_layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton("⏹ STOP")
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet("background-color: #FF453A; color: white; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        self.btn_stop.clicked.connect(self._stop_playback)
        ctrl_layout.addWidget(self.btn_stop)

        ctrl_layout.addSpacing(10)

        lbl_vol = QLabel("🔊")
        lbl_vol.setStyleSheet("font-size: 11px;")
        ctrl_layout.addWidget(lbl_vol)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #2C2C2E; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #8E8E93; border-radius: 2px; }
            QSlider::handle:horizontal { background: #8E8E93; width: 10px; margin-top: -3px; margin-bottom: -3px; border-radius: 5px; }
        """)
        self.vol_slider.valueChanged.connect(lambda v: self.audio_engine.set_master_volume(v / 100.0))
        ctrl_layout.addWidget(self.vol_slider)

        ctrl_layout.addStretch()
        player_layout.addLayout(ctrl_layout)

        main_layout.addWidget(self.player_card, stretch=1)

    def update_cover_image(self, pil_image):
        if pil_image:
            try:
                buf = io.BytesIO()
                pil_image.save(buf, format="PNG")
                qimg = QImage.fromData(buf.getvalue())
                pixmap = QPixmap.fromImage(qimg).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_cover_art.setPixmap(pixmap)
                self.lbl_cover_art.setText("")
                return
            except Exception as e:
                print(f"Error cargando pixmap: {e}")
        
        self.lbl_cover_art.setPixmap(QPixmap())
        self.lbl_cover_art.setText("💿")

    def render_mixer_sliders(self, stem_names):
        self.current_stems = stem_names
        
        # Clear existing widgets in grid
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.slider_widgets = {}
        self.mute_buttons = {}
        self.solo_buttons = {}

        is_6s = len(stem_names) >= 5 or any(s in stem_names for s in ["PIANO", "GUITAR"])
        layout = STEM_LAYOUT_6S if is_6s else STEM_LAYOUT_4S

        for stem, row, col in layout:
            if stem not in stem_names and not is_6s and stem != "OTHER":
                continue

            cell = QFrame()
            cell.setStyleSheet("background-color: #121214; border-radius: 8px;")
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(4, 4, 4, 4)
            cell_layout.setSpacing(2)

            # Mute & Solo Header
            ms_layout = QHBoxLayout()
            btn_m = QPushButton("M")
            btn_m.setFixedSize(20, 18)
            btn_m.setStyleSheet("background-color: #2C2C2E; color: white; font-size: 8px; font-weight: bold; border-radius: 3px;")
            btn_m.clicked.connect(lambda _, s=stem: self._toggle_mute(s))
            ms_layout.addWidget(btn_m)
            self.mute_buttons[stem] = btn_m

            ms_layout.addStretch()

            btn_s = QPushButton("S")
            btn_s.setFixedSize(20, 18)
            btn_s.setStyleSheet("background-color: #2C2C2E; color: white; font-size: 8px; font-weight: bold; border-radius: 3px;")
            btn_s.clicked.connect(lambda _, s=stem: self._toggle_solo(s))
            ms_layout.addWidget(btn_s)
            self.solo_buttons[stem] = btn_s

            cell_layout.addLayout(ms_layout)

            # Vertical Slider
            slider = QSlider(Qt.Vertical)
            slider.setRange(0, 100)
            slider.setValue(100)
            slider.setStyleSheet("""
                QSlider::groove:vertical { width: 4px; background: #2C2C2E; border-radius: 2px; }
                QSlider::sub-page:vertical { background: #0A84FF; border-radius: 2px; }
                QSlider::handle:vertical { background: #0A84FF; height: 10px; margin-left: -3px; margin-right: -3px; border-radius: 5px; }
            """)
            slider.valueChanged.connect(lambda v, s=stem: self.audio_engine.set_stem_volume(s, v / 100.0))
            cell_layout.addWidget(slider, alignment=Qt.AlignCenter)
            self.slider_widgets[stem] = slider

            # Stem Name Label
            lbl = QLabel(stem)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 9px; font-weight: bold; color: #FFFFFF;")
            cell_layout.addWidget(lbl)

            self.grid_layout.addWidget(cell, row, col)

    def _toggle_mute(self, stem):
        curr = self.audio_engine.stem_mutes.get(stem, False)
        new_state = not curr
        self.audio_engine.set_stem_mute(stem, new_state)
        btn = self.mute_buttons.get(stem)
        if btn:
            btn.setStyleSheet(f"background-color: {'#FF453A' if new_state else '#2C2C2E'}; color: white; font-size: 8px; font-weight: bold; border-radius: 3px;")

    def _toggle_solo(self, stem):
        curr = self.audio_engine.stem_solos.get(stem, False)
        new_state = not curr
        self.audio_engine.set_stem_solo(stem, new_state)
        btn = self.solo_buttons.get(stem)
        if btn:
            btn.setStyleSheet(f"background-color: {'#FF9F0A' if new_state else '#2C2C2E'}; color: white; font-size: 8px; font-weight: bold; border-radius: 3px;")

    def load_track_info(self, title, artist, mode, cover_image=None, stems=None):
        self.lbl_cover_title.setText(title)
        self.lbl_cover_artist.setText(artist)
        self.lbl_now_playing.setText(f"[{mode}] {title}")
        self.update_cover_image(cover_image)

        if stems:
            self.render_mixer_sliders(stems)
        else:
            self.render_mixer_sliders(["PISTA COMPLETA"])

    def _toggle_play_pause(self):
        if not self.audio_engine.mode:
            return

        if not self.audio_engine.is_playing:
            self.audio_engine.play()
            self.btn_play.setText("⏸ PAUSE")
            self.btn_play.setStyleSheet("background-color: #FF9F0A; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        elif self.audio_engine.is_paused:
            self.audio_engine.pause()
            self.btn_play.setText("⏸ PAUSE")
            self.btn_play.setStyleSheet("background-color: #FF9F0A; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        else:
            self.audio_engine.pause()
            self.btn_play.setText("▶ PLAY")
            self.btn_play.setStyleSheet("background-color: #30D158; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")

    def _stop_playback(self):
        self.audio_engine.stop()
        self.btn_play.setText("▶ PLAY")
        self.btn_play.setStyleSheet("background-color: #30D158; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        self.seek_slider.setValue(0)

    def _on_seek_pressed(self):
        self.is_user_seeking = True

    def _on_seek_released(self):
        target_sec = (self.seek_slider.value() / 1000.0) * self.audio_engine.duration
        self.audio_engine.seek(target_sec)
        self.is_user_seeking = False

    def update_player_loop(self):
        if self.audio_engine.is_playing and not self.is_user_seeking:
            curr_pos = self.audio_engine.get_current_position()
            dur = self.audio_engine.duration
            if dur > 0:
                pct = int((curr_pos / dur) * 1000.0)
                self.seek_slider.setValue(pct)
                self.lbl_time.setText(f"{self._format_time(curr_pos)} / {self._format_time(dur)}")

    def _on_playback_finished(self):
        self.btn_play.setText("▶ PLAY")
        self.btn_play.setStyleSheet("background-color: #30D158; color: white; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        self.seek_slider.setValue(0)

    @staticmethod
    def _format_time(seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
