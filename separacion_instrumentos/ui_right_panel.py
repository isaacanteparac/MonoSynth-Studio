import os
import subprocess
import customtkinter as ctk

class RightPanel(ctk.CTkFrame):
    def __init__(self, parent, config_manager, on_play_stems_callback):
        super().__init__(parent, fg_color="transparent")
        self.config = config_manager
        self.on_play_stems_callback = on_play_stems_callback
        self.selected_folder = None

        self._create_ui()
        self.refresh_divided_songs()

    def _create_ui(self):
        # Card Block: Divided Songs (monosync)
        self.block_card = ctk.CTkFrame(self, fg_color="#1C1C1E", corner_radius=14, border_width=1, border_color="#2C2C2E")
        self.block_card.pack(fill="both", expand=True)

        # Header Frame
        header = ctk.CTkFrame(self.block_card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 8))

        lbl_title = ctk.CTkLabel(
            header,
            text="Canciones Divididas",
            font=("SF Pro Display", 14, "bold"),
            text_color="#F2F2F7"
        )
        lbl_title.pack(side="left")

        btn_refresh = ctk.CTkButton(
            header,
            text="🔄 Actualizar",
            width=80,
            height=26,
            font=("SF Pro Text", 10, "bold"),
            fg_color="#2C2C2E",
            hover_color="#3A3A3C",
            corner_radius=6,
            command=self.refresh_divided_songs
        )
        btn_refresh.pack(side="right")

        lbl_tree_root = ctk.CTkLabel(
            self.block_card,
            text="📁  monosync  (Carpeta Principal)",
            font=("SF Pro Display", 12, "bold"),
            text_color="#30D158"
        )
        lbl_tree_root.pack(anchor="w", padx=15, pady=(0, 6))

        # Scrollable Tree / List of separated songs
        self.scroll_tree = ctk.CTkScrollableFrame(self.block_card, fg_color="#121214", corner_radius=10)
        self.scroll_tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Action Buttons for selected divided track
        actions_frame = ctk.CTkFrame(self.block_card, fg_color="#252528", corner_radius=10)
        actions_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_play_stems = ctk.CTkButton(
            actions_frame,
            text="🎛 Cargar Mezclador Stems",
            state="disabled",
            height=34,
            font=("SF Pro Text", 11, "bold"),
            fg_color="#0A84FF",
            hover_color="#0066CC",
            corner_radius=8,
            command=self._cargar_mezclador
        )
        self.btn_play_stems.pack(fill="x", padx=10, pady=8)

    def refresh_divided_songs(self):
        for widget in self.scroll_tree.winfo_children():
            widget.destroy()

        output_dir = self.config.get("output_dir", os.path.abspath("monosync"))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        items = os.listdir(output_dir)
        folders = [f for f in items if os.path.isdir(os.path.join(output_dir, f)) and not f.startswith("_")]

        if not folders:
            lbl_empty = ctk.CTkLabel(
                self.scroll_tree,
                text="No hay canciones divididas todavia.\nUsa el panel de la izquierda para separar.",
                font=("SF Pro Text", 11, "italic"),
                text_color="#636366"
            )
            lbl_empty.pack(pady=30)
            self.btn_play_stems.configure(state="disabled")
            return

        for folder_name in folders:
            folder_path = os.path.join(output_dir, folder_name)
            is_sel = (folder_path == self.selected_folder)

            # Folder Card Item
            card = ctk.CTkFrame(
                self.scroll_tree,
                fg_color="#0A84FF" if is_sel else "#1C1C1E",
                corner_radius=8
            )
            card.pack(fill="x", pady=4, padx=2)

            btn_folder = ctk.CTkButton(
                card,
                text=f"📂  {folder_name}",
                anchor="w",
                font=("SF Pro Text", 12, "bold"),
                fg_color="transparent",
                text_color="#FFFFFF" if is_sel else "#F2F2F7",
                hover_color="#2C2C2E",
                height=32,
                command=lambda p=folder_path: self._select_folder(p)
            )
            btn_folder.pack(fill="x", padx=5, pady=(4, 0))

            # List stems detected inside folder
            stems_found = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
            stems_text = " • ".join([s.replace(".wav", "").upper() for s in stems_found])

            lbl_stems = ctk.CTkLabel(
                card,
                text=f"└──  {stems_text}",
                font=("SF Pro Text", 10),
                text_color="#EBEBF5" if is_sel else "#8E8E93"
            )
            lbl_stems.pack(anchor="w", padx=24, pady=(0, 6))

    def _select_folder(self, folder_path):
        self.selected_folder = folder_path
        self.refresh_divided_songs()
        self.btn_play_stems.configure(state="normal")

    def _cargar_mezclador(self):
        if self.selected_folder and os.path.exists(self.selected_folder):
            song_name = os.path.basename(self.selected_folder)
            stems_found = [f.replace(".wav", "").upper() for f in os.listdir(self.selected_folder) if f.endswith(".wav")]
            
            # Standard order: VOCALS, DRUMS, BASS, PIANO, GUITAR, OTHER
            preferred_order = ["VOCALS", "DRUMS", "BASS", "PIANO", "GUITAR", "OTHER"]
            ordered_stems = [s for s in preferred_order if s in stems_found]
            for s in stems_found:
                if s not in ordered_stems:
                    ordered_stems.append(s)

            self.on_play_stems_callback(self.selected_folder, song_name, ordered_stems)
