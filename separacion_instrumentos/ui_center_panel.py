import os
import customtkinter as ctk

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

STEM_LAYOUT_6S = [
    ("VOCALS", 0, 0), ("DRUMS", 0, 1), ("BASS", 0, 2),
    ("PIANO", 1, 0),  ("GUITAR", 1, 1), ("OTHER", 1, 2)
]

STEM_LAYOUT_4S = [
    ("VOCALS", 0, 0), ("DRUMS", 0, 1), ("BASS", 0, 2),
    ("OTHER", 1, 1)  # Centered in row 1
]

class CenterPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, audio_engine):
        super().__init__(parent, fg_color="transparent")
        self.config = config_manager
        self.audio_engine = audio_engine

        self.current_stems = ["VOCALS", "DRUMS", "BASS", "PIANO", "GUITAR", "OTHER"]
        self.slider_widgets = {}
        self.mute_buttons = {}
        self.solo_buttons = {}
        self.is_user_seeking = False

        self._create_cover_block()
        self._create_mixer_block()
        self._create_player_block()

        self.audio_engine.on_finish_callback = self._on_playback_finished

    def _create_cover_block(self):
        self.block_cover = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=14, border_width=1, border_color="#2C2C2E")
        self.block_cover.pack(side="top", fill="both", expand=True, pady=(0, 10))

        self.cover_container = ctk.CTkFrame(self.block_cover, fg_color="#121214", corner_radius=12)
        self.cover_container.pack(fill="both", expand=True, padx=15, pady=10)

        self.lbl_cover_art = ctk.CTkLabel(
            self.cover_container,
            text="💿",
            font=("SF Pro Display", 48)
        )
        self.lbl_cover_art.pack(expand=True, pady=(8, 2))

        self.lbl_cover_artist = ctk.CTkLabel(
            self.cover_container,
            text="",
            font=("SF Pro Text", 11),
            text_color="#8E8E93"
        )
        self.lbl_cover_artist.pack()

        self.lbl_cover_title = ctk.CTkLabel(
            self.cover_container,
            text="Selecciona una canción",
            font=("SF Pro Display", 13, "bold"),
            text_color="#F2F2F7"
        )
        self.lbl_cover_title.pack(pady=(0, 8))

    def update_cover_image(self, pil_image):
        if HAS_PIL and pil_image:
            try:
                pil_resized = pil_image.resize((150, 150), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_resized, dark_image=pil_resized, size=(150, 150))
                self.lbl_cover_art.configure(image=ctk_img, text="")
                return
            except Exception as e:
                print(f"Error renderizando cover image: {e}")
        
        self.lbl_cover_art.configure(image=None, text="💿", font=("SF Pro Display", 48))

    def _create_mixer_block(self):
        # Card Block: Individual Stem Mixer (2 rows layout)
        self.block_mixer = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=14, border_width=1, border_color="#2C2C2E", height=320)
        self.block_mixer.pack(side="top", fill="x", pady=(0, 10))
        self.block_mixer.pack_propagate(False)

        header = ctk.CTkLabel(
            self.block_mixer,
            text="Mezclador de Instrumentos",
            font=("SF Pro Display", 13, "bold"),
            text_color="#F2F2F7"
        )
        header.pack(anchor="w", padx=15, pady=(8, 2))

        self.mixer_inner = ctk.CTkFrame(self.block_mixer, fg_color="transparent")
        self.mixer_inner.pack(fill="both", expand=True, padx=10, pady=(2, 8))

        self.render_mixer_sliders(self.current_stems)

    def render_mixer_sliders(self, stem_names):
        self.current_stems = stem_names
        for w in self.mixer_inner.winfo_children():
            w.destroy()

        self.slider_widgets = {}
        self.mute_buttons = {}
        self.solo_buttons = {}

        # Configure 3x2 Grid inside mixer_inner
        for col in range(3):
            self.mixer_inner.grid_columnconfigure(col, weight=1)
        for row in range(2):
            self.mixer_inner.grid_rowconfigure(row, weight=1)

        # Determine layout mapping
        is_6s = len(stem_names) >= 5 or any(s in stem_names for s in ["PIANO", "GUITAR"])
        layout = STEM_LAYOUT_6S if is_6s else STEM_LAYOUT_4S

        for stem, row, col in layout:
            if stem not in stem_names and not is_6s and stem != "OTHER":
                continue

            cell = ctk.CTkFrame(self.mixer_inner, fg_color="#121214", corner_radius=8)
            cell.grid(row=row, column=col, sticky="nsew", padx=4, pady=3)

            # Header Mute & Solo
            ms_frame = ctk.CTkFrame(cell, fg_color="transparent")
            ms_frame.pack(fill="x", padx=2, pady=(3, 1))

            btn_m = ctk.CTkButton(
                ms_frame, text="M", width=18, height=16,
                font=("SF Pro Text", 8, "bold"),
                fg_color="#2C2C2E", hover_color="#FF453A",
                corner_radius=4,
                command=lambda s=stem: self._toggle_mute(s)
            )
            btn_m.pack(side="left", padx=1)
            self.mute_buttons[stem] = btn_m

            btn_s = ctk.CTkButton(
                ms_frame, text="S", width=18, height=16,
                font=("SF Pro Text", 8, "bold"),
                fg_color="#2C2C2E", hover_color="#FF9F0A",
                corner_radius=4,
                command=lambda s=stem: self._toggle_solo(s)
            )
            btn_s.pack(side="right", padx=1)
            self.solo_buttons[stem] = btn_s

            # Vertical Volume Slider
            slider = ctk.CTkSlider(
                cell,
                orientation="vertical",
                from_=1.0,
                to=0.0,
                height=75,
                button_color="#0A84FF",
                button_hover_color="#0066CC",
                progress_color="#0A84FF",
                command=lambda v, s=stem: self.audio_engine.set_stem_volume(s, v)
            )
            slider.set(1.0) # Full 100% volume by default
            slider.pack(expand=True, pady=2)
            self.slider_widgets[stem] = slider

            # Stem Instrument Label
            lbl = ctk.CTkLabel(
                cell,
                text=stem,
                font=("SF Pro Text", 9, "bold"),
                text_color="#FFFFFF"
            )
            lbl.pack(pady=(0, 3))

    def _toggle_mute(self, stem):
        curr = self.audio_engine.stem_mutes.get(stem, False)
        new_state = not curr
        self.audio_engine.set_stem_mute(stem, new_state)
        btn = self.mute_buttons.get(stem)
        if btn:
            btn.configure(fg_color="#FF453A" if new_state else "#2C2C2E")

    def _toggle_solo(self, stem):
        curr = self.audio_engine.stem_solos.get(stem, False)
        new_state = not curr
        self.audio_engine.set_stem_solo(stem, new_state)
        btn = self.solo_buttons.get(stem)
        if btn:
            btn.configure(fg_color="#FF9F0A" if new_state else "#2C2C2E")

    def _create_player_block(self):
        self.block_player = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=14, border_width=1, border_color="#2C2C2E")
        self.block_player.pack(side="bottom", fill="x", pady=(0, 0))

        info_frame = ctk.CTkFrame(self.block_player, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(8, 0))

        self.lbl_now_playing = ctk.CTkLabel(
            info_frame,
            text="Sin reproducción",
            font=("SF Pro Display", 12, "bold"),
            text_color="#F2F2F7"
        )
        self.lbl_now_playing.pack(side="left")

        self.lbl_time = ctk.CTkLabel(
            info_frame,
            text="00:00 / 00:00",
            font=("SF Pro Text", 11),
            text_color="#8E8E93"
        )
        self.lbl_time.pack(side="right")

        self.seek_slider = ctk.CTkSlider(
            self.block_player,
            from_=0,
            to=100,
            button_color="#30D158",
            button_hover_color="#248A3D",
            progress_color="#30D158",
            command=self._on_seek_drag
        )
        self.seek_slider.set(0)
        self.seek_slider.pack(fill="x", padx=15, pady=4)
        self.seek_slider.bind("<ButtonRelease-1>", self._on_seek_release)

        ctrl_frame = ctk.CTkFrame(self.block_player, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=15, pady=(0, 8))

        self.btn_play_pause = ctk.CTkButton(
            ctrl_frame,
            text="▶  PLAY",
            width=90,
            height=30,
            font=("SF Pro Text", 11, "bold"),
            fg_color="#30D158",
            hover_color="#248A3D",
            corner_radius=8,
            command=self._toggle_play_pause
        )
        self.btn_play_pause.pack(side="left", padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            ctrl_frame,
            text="⏹ STOP",
            width=75,
            height=30,
            font=("SF Pro Text", 11, "bold"),
            fg_color="#FF453A",
            hover_color="#D70015",
            corner_radius=8,
            command=self._stop_playback
        )
        self.btn_stop.pack(side="left", padx=(0, 12))

        lbl_vol_icon = ctk.CTkLabel(ctrl_frame, text="🔊", font=("SF Pro Text", 11))
        lbl_vol_icon.pack(side="left", padx=(8, 4))

        self.master_vol_slider = ctk.CTkSlider(
            ctrl_frame,
            from_=0.0,
            to=1.0,
            width=90,
            button_color="#8E8E93",
            progress_color="#8E8E93",
            command=lambda v: self.audio_engine.set_master_volume(v)
        )
        self.master_vol_slider.set(1.0)
        self.master_vol_slider.pack(side="left")

    def load_track_info(self, title, artist, mode, cover_image=None, stems=None):
        self.lbl_cover_title.configure(text=title)
        self.lbl_cover_artist.configure(text=artist)
        self.lbl_now_playing.configure(text=f"[{mode}] {title}")
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
            self.btn_play_pause.configure(text="⏸ PAUSE", fg_color="#FF9F0A")
        elif self.audio_engine.is_paused:
            self.audio_engine.pause()
            self.btn_play_pause.configure(text="⏸ PAUSE", fg_color="#FF9F0A")
        else:
            self.audio_engine.pause()
            self.btn_play_pause.configure(text="▶  PLAY", fg_color="#30D158")

    def _stop_playback(self):
        self.audio_engine.stop()
        self.btn_play_pause.configure(text="▶  PLAY", fg_color="#30D158")
        self.seek_slider.set(0)
        self.lbl_time.configure(text=f"00:00 / {self._format_time(self.audio_engine.duration)}")

    def _on_seek_drag(self, val):
        self.is_user_seeking = True

    def _on_seek_release(self, event):
        target_sec = (self.seek_slider.get() / 100.0) * self.audio_engine.duration
        self.audio_engine.seek(target_sec)
        self.is_user_seeking = False

    def update_player_loop(self):
        if self.audio_engine.is_playing and not self.is_user_seeking:
            curr_pos = self.audio_engine.get_current_position()
            dur = self.audio_engine.duration
            if dur > 0:
                pct = (curr_pos / dur) * 100.0
                self.seek_slider.set(pct)
                self.lbl_time.configure(text=f"{self._format_time(curr_pos)} / {self._format_time(dur)}")
        
        self.after(100, self.update_player_loop)

    def _on_playback_finished(self):
        self.btn_play_pause.configure(text="▶  PLAY", fg_color="#30D158")
        self.seek_slider.set(0)

    @staticmethod
    def _format_time(seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
