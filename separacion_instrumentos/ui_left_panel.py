import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from metadata_utils import get_song_metadata

AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"]

class LeftPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, audio_engine, separator, on_song_select_callback):
        super().__init__(parent, fg_color="transparent")
        self.config = config_manager
        self.audio_engine = audio_engine
        self.separator = separator
        self.on_song_select_callback = on_song_select_callback

        # Store songs metadata: list of dicts {"path": str, "artist": str, "title": str, "cover_image": PIL}
        self.songs_data = []
        self.artist_expanded = {} # {"Artist Name": True/False}
        self.selected_song_path = None

        self._create_top_block()
        self._create_bottom_block()

    def _create_top_block(self):
        # Card Block: Undivided Songs List
        self.block_top = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=14, border_width=1, border_color="#2C2C2E")
        self.block_top.pack(side="top", fill="both", expand=True, pady=(0, 10))

        # Title Header
        header_frame = ctk.CTkFrame(self.block_top, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 4))

        lbl_title = ctk.CTkLabel(
            header_frame,
            text="Canciones Sin Dividir",
            font=("SF Pro Display", 14, "bold"),
            text_color="#F2F2F7"
        )
        lbl_title.pack(side="left")

        # Buttons to Add Folder or Files
        btn_folder = ctk.CTkButton(
            header_frame,
            text="📂 Carpeta",
            width=70,
            height=26,
            font=("SF Pro Text", 10, "bold"),
            fg_color="#0A84FF",
            hover_color="#0066CC",
            corner_radius=6,
            command=self._agregar_carpeta
        )
        btn_folder.pack(side="right", padx=(4, 0))

        btn_files = ctk.CTkButton(
            header_frame,
            text="📄 Archivos",
            width=70,
            height=26,
            font=("SF Pro Text", 10, "bold"),
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            corner_radius=6,
            command=self._agregar_archivos
        )
        btn_files.pack(side="right")

        # Status / Queue Info Badge
        self.lbl_queue_status = ctk.CTkLabel(
            self.block_top,
            text="Cola vacía",
            font=("SF Pro Text", 11),
            text_color="#8E8E93"
        )
        self.lbl_queue_status.pack(anchor="w", padx=15, pady=(0, 4))

        # Scrollable Accordion List Container
        self.scroll_songs = ctk.CTkScrollableFrame(self.block_top, fg_color="#121214", corner_radius=10)
        self.scroll_songs.pack(fill="both", expand=True, padx=15, pady=4)

        # Selected Song Action Buttons Container
        self.actions_frame = ctk.CTkFrame(self.block_top, fg_color="#252528", corner_radius=10)
        self.actions_frame.pack(fill="x", padx=15, pady=(4, 6))

        btns_sub = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        btns_sub.pack(fill="x", padx=6, pady=6)

        self.btn_listen_solo = ctk.CTkButton(
            btns_sub,
            text="🎧 Escuchar Sola",
            state="disabled",
            height=30,
            font=("SF Pro Text", 11, "bold"),
            fg_color="#30D158",
            hover_color="#248A3D",
            corner_radius=8,
            command=self._escuchar_sola
        )
        self.btn_listen_solo.pack(side="left", expand=True, fill="x", padx=(0, 3))

        self.btn_queue_add = ctk.CTkButton(
            btns_sub,
            text="➕ Añadir a Cola",
            state="disabled",
            height=30,
            font=("SF Pro Text", 11, "bold"),
            fg_color="#BF5AF2",
            hover_color="#8E24AA",
            corner_radius=8,
            command=self._anadir_a_cola
        )
        self.btn_queue_add.pack(side="right", expand=True, fill="x", padx=(3, 0))

        # Big "INICIAR CONVERSIÓN" Button
        self.btn_start_conversion = ctk.CTkButton(
            self.block_top,
            text="🚀 INICIAR CONVERSIÓN",
            height=38,
            font=("SF Pro Text", 13, "bold"),
            fg_color="#FF9F0A",
            hover_color="#D68000",
            corner_radius=10,
            command=self._iniciar_conversion
        )
        self.btn_start_conversion.pack(fill="x", padx=15, pady=(0, 12))

    def _create_bottom_block(self):
        # Card Block: Conversion & System Settings
        self.block_bottom = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=14, border_width=1, border_color="#2C2C2E")
        self.block_bottom.pack(side="bottom", fill="x", expand=False)

        lbl_title = ctk.CTkLabel(
            self.block_bottom,
            text="Configuración de Conversión",
            font=("SF Pro Display", 13, "bold"),
            text_color="#F2F2F7"
        )
        lbl_title.pack(anchor="w", padx=15, pady=(10, 4))

        # Automatic FFmpeg status badge (no button required)
        ff_frame = ctk.CTkFrame(self.block_bottom, fg_color="#252528", corner_radius=8)
        ff_frame.pack(fill="x", padx=15, pady=4)

        current_ff = self.config.get("ffmpeg_path", "")
        self.lbl_ff_status = ctk.CTkLabel(
            ff_frame,
            text="FFmpeg: Automático (Detectado en carpeta)",
            font=("SF Pro Text", 10, "bold"),
            text_color="#30D158"
        )
        self.lbl_ff_status.pack(side="left", padx=10, pady=6)

        # Instrument Stems Model (4s vs 6s)
        lbl_stems = ctk.CTkLabel(
            self.block_bottom,
            text="Cantidad de Instrumentos:",
            font=("SF Pro Text", 11),
            text_color="#8E8E93"
        )
        lbl_stems.pack(anchor="w", padx=15, pady=(6, 2))

        current_model = self.config.get("model", "htdemucs")
        self.seg_stems = ctk.CTkSegmentedButton(
            self.block_bottom,
            values=["4 Instrumentos (4S)", "6 Instrumentos (6S)"],
            selected_color="#0A84FF",
            font=("SF Pro Text", 11),
            command=self._on_model_change
        )
        self.seg_stems.set("6 Instrumentos (6S)" if "6s" in current_model else "4 Instrumentos (4S)")
        self.seg_stems.pack(fill="x", padx=15, pady=(0, 6))

        # Hardware Device (CPU vs CUDA)
        lbl_dev = ctk.CTkLabel(
            self.block_bottom,
            text="Procesamiento (Hardware):",
            font=("SF Pro Text", 11),
            text_color="#8E8E93"
        )
        lbl_dev.pack(anchor="w", padx=15, pady=(4, 2))

        current_dev = self.config.get("device", "cpu")
        self.seg_device = ctk.CTkSegmentedButton(
            self.block_bottom,
            values=["CPU", "CUDA (GPU NVIDIA)"],
            selected_color="#30D158",
            font=("SF Pro Text", 11),
            command=self._on_device_change
        )
        self.seg_device.set("CUDA (GPU NVIDIA)" if current_dev == "cuda" else "CPU")
        self.seg_device.pack(fill="x", padx=15, pady=(0, 12))

    def _agregar_carpeta(self):
        folder_path = filedialog.askdirectory(title="Seleccionar carpeta de música")
        if folder_path:
            added = 0
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in AUDIO_EXTENSIONS:
                        full_p = os.path.join(root, f)
                        if not any(s["path"] == full_p for s in self.songs_data):
                            meta = get_song_metadata(full_p)
                            meta["path"] = full_p
                            self.songs_data.append(meta)
                            if meta["artist"] not in self.artist_expanded:
                                self.artist_expanded[meta["artist"]] = True
                            added += 1
            self._render_accordion()

    def _agregar_archivos(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccionar canciones",
            filetypes=[("Archivos de Audio", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg")]
        )
        if rutas:
            for r in rutas:
                if not any(s["path"] == r for s in self.songs_data):
                    meta = get_song_metadata(r)
                    meta["path"] = r
                    self.songs_data.append(meta)
                    if meta["artist"] not in self.artist_expanded:
                        self.artist_expanded[meta["artist"]] = True
            self._render_accordion()

    def _render_accordion(self):
        for widget in self.scroll_songs.winfo_children():
            widget.destroy()

        if not self.songs_data:
            lbl_empty = ctk.CTkLabel(
                self.scroll_songs,
                text="No hay canciones o carpetas agregadas.\nUsa los botones superiores.",
                font=("SF Pro Text", 11, "italic"),
                text_color="#636366"
            )
            lbl_empty.pack(pady=20)
            return

        # Group songs by Artist
        artist_map = {}
        for song in self.songs_data:
            art = song["artist"]
            if art not in artist_map:
                artist_map[art] = []
            artist_map[art].append(song)

        for artist_name, songs in artist_map.items():
            is_expanded = self.artist_expanded.get(artist_name, True)
            arrow = "▼" if is_expanded else "▶"

            # Artist Accordion Header Frame
            artist_card = ctk.CTkFrame(self.scroll_songs, fg_color="#1C1C1E", corner_radius=8)
            artist_card.pack(fill="x", pady=3)

            btn_toggle = ctk.CTkButton(
                artist_card,
                text=f"{arrow}  👤 {artist_name} ({len(songs)})",
                anchor="w",
                font=("SF Pro Text", 11, "bold"),
                fg_color="transparent",
                text_color="#F2F2F7",
                hover_color="#2C2C2E",
                height=30,
                command=lambda a=artist_name: self._toggle_artist(a)
            )
            btn_toggle.pack(fill="x", padx=4, pady=2)

            # Render child songs if expanded
            if is_expanded:
                songs_container = ctk.CTkFrame(artist_card, fg_color="transparent")
                songs_container.pack(fill="x", padx=12, pady=(0, 4))

                for s in songs:
                    path = s["path"]
                    title = s["title"]
                    is_selected = (path == self.selected_song_path)

                    btn_song = ctk.CTkButton(
                        songs_container,
                        text=f"🎵 {title}",
                        anchor="w",
                        font=("SF Pro Text", 11),
                        fg_color="#0A84FF" if is_selected else "#121214",
                        text_color="#FFFFFF" if is_selected else "#D1D1D6",
                        hover_color="#2C2C2E",
                        height=28,
                        corner_radius=6,
                        command=lambda item=s: self._select_song(item)
                    )
                    btn_song.pack(fill="x", pady=2)

    def _toggle_artist(self, artist_name):
        curr = self.artist_expanded.get(artist_name, True)
        self.artist_expanded[artist_name] = not curr
        self._render_accordion()

    def _select_song(self, song_meta):
        self.selected_song_path = song_meta["path"]
        self._render_accordion()
        self.btn_listen_solo.configure(state="normal")
        self.btn_queue_add.configure(state="normal")
        
        # Pass metadata including cover image to parent
        self.on_song_select_callback(song_meta, mode="single_preview")

    def _escuchar_sola(self):
        if self.selected_song_path and os.path.exists(self.selected_song_path):
            song_meta = next((s for s in self.songs_data if s["path"] == self.selected_song_path), None)
            if song_meta:
                self.on_song_select_callback(song_meta, mode="single_play")

    def _anadir_a_cola(self):
        if self.selected_song_path:
            self.separator.add_to_queue([self.selected_song_path])
            self.update_queue_status()

    def _iniciar_conversion(self):
        # Auto-add all loaded undivided songs to queue if queue is empty
        if self.separator.get_queue_size() == 0 and self.songs_data:
            all_paths = [s["path"] for s in self.songs_data]
            self.separator.add_to_queue(all_paths)

        started = self.separator.start_processing()
        self.update_queue_status()

    def update_queue_status(self):
        size = self.separator.get_queue_size()
        curr = self.separator.current_item
        if curr:
            self.lbl_queue_status.configure(
                text=f"Procesando: {curr} ({size} en espera)",
                text_color="#FF9F0A"
            )
        elif size > 0:
            self.lbl_queue_status.configure(
                text=f"{size} en cola (pulsa Iniciar)",
                text_color="#0A84FF"
            )
        else:
            self.lbl_queue_status.configure(
                text="Cola vacía",
                text_color="#8E8E93"
            )

    def _on_model_change(self, val):
        model_name = "htdemucs_6s" if "6S" in val else "htdemucs"
        self.config.set("model", model_name)

    def _on_device_change(self, val):
        dev = "cuda" if "CUDA" in val else "cpu"
        self.config.set("device", dev)
