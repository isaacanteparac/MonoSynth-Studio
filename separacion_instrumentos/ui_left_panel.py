import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QFileDialog, QRadioButton, QButtonGroup, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread
from metadata_utils import get_song_metadata

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}

class FolderScannerThread(QThread):
    song_found = Signal(dict)
    finished_scan = Signal(int)

    def __init__(self, folder_path, existing_paths):
        super().__init__()
        self.folder_path = folder_path
        self.existing_paths = existing_paths

    def run(self):
        count = 0
        for root, _, files in os.walk(self.folder_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in AUDIO_EXTENSIONS:
                    full_p = os.path.join(root, f)
                    if full_p not in self.existing_paths:
                        meta = get_song_metadata(full_p)
                        meta["path"] = full_p
                        self.song_found.emit(meta)
                        count += 1
        self.finished_scan.emit(count)

class LeftPanel(QWidget):
    song_selected = Signal(dict, str) # (song_meta, mode)
    model_changed = Signal(str)

    def __init__(self, config_manager, audio_engine, separator):
        super().__init__()
        self.config = config_manager
        self.audio_engine = audio_engine
        self.separator = separator

        self.songs_data = []
        self.artist_items = {} # {"Artist": QTreeWidgetItem}
        self.selected_song_meta = None

        self._create_ui()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # TOP CARD BLOCK: Undivided Songs & Queue Box
        self.top_card = QFrame()
        self.top_card.setObjectName("CardBlock")
        top_layout = QVBoxLayout(self.top_card)
        top_layout.setContentsMargins(12, 12, 12, 12)
        top_layout.setSpacing(8)

        # Header Row
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Canciones Sin Dividir")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #F2F2F7;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()

        btn_folder = QPushButton("📂 Carpeta")
        btn_folder.setCursor(Qt.PointingHandCursor)
        btn_folder.setStyleSheet("background-color: #0A84FF; color: white; border-radius: 6px; font-weight: bold; padding: 4px 10px;")
        btn_folder.clicked.connect(self._agregar_carpeta)
        header_layout.addWidget(btn_folder)

        btn_files = QPushButton("📄 Archivos")
        btn_files.setCursor(Qt.PointingHandCursor)
        btn_files.setStyleSheet("background-color: #2C2C2E; color: white; border-radius: 6px; font-weight: bold; padding: 4px 10px;")
        btn_files.clicked.connect(self._agregar_archivos)
        header_layout.addWidget(btn_files)

        top_layout.addLayout(header_layout)

        self.lbl_scan_status = QLabel("")
        self.lbl_scan_status.setStyleSheet("font-size: 10px; color: #30D158; font-style: italic;")
        top_layout.addWidget(self.lbl_scan_status)

        # Native Qt Tree Widget (Ultra-fast Collapsible Accordion by Artist)
        self.tree_songs = QTreeWidget()
        self.tree_songs.setHeaderHidden(True)
        self.tree_songs.setStyleSheet("""
            QTreeWidget {
                background-color: #121214;
                border: none;
                border-radius: 8px;
                color: #D1D1D6;
                padding: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0A84FF;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #2C2C2E;
            }
        """)
        self.tree_songs.itemClicked.connect(self._on_item_clicked)
        top_layout.addWidget(self.tree_songs, stretch=3)

        # Actions Buttons Frame
        action_layout = QHBoxLayout()

        self.btn_listen_solo = QPushButton("🎧 Escuchar Sola")
        self.btn_listen_solo.setEnabled(False)
        self.btn_listen_solo.setCursor(Qt.PointingHandCursor)
        self.btn_listen_solo.setStyleSheet("background-color: #30D158; color: white; font-weight: bold; padding: 6px; border-radius: 6px;")
        self.btn_listen_solo.clicked.connect(self._escuchar_sola)
        action_layout.addWidget(self.btn_listen_solo)

        self.btn_queue_add = QPushButton("➕ Añadir a Cola")
        self.btn_queue_add.setEnabled(False)
        self.btn_queue_add.setCursor(Qt.PointingHandCursor)
        self.btn_queue_add.setStyleSheet("background-color: #BF5AF2; color: white; font-weight: bold; padding: 6px; border-radius: 6px;")
        self.btn_queue_add.clicked.connect(self._anadir_a_cola)
        action_layout.addWidget(self.btn_queue_add)

        top_layout.addLayout(action_layout)

        # QUEUE BOX CONTAINER
        self.lbl_queue_title = QLabel("📋 Cola de Conversión (0)")
        self.lbl_queue_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #FF9F0A; margin-top: 4px;")
        top_layout.addWidget(self.lbl_queue_title)

        self.list_queue = QListWidget()
        self.list_queue.setStyleSheet("""
            QListWidget {
                background-color: #121214;
                border: none;
                border-radius: 6px;
                color: #8E8E93;
                font-size: 11px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #1C1C1E;
            }
        """)
        top_layout.addWidget(self.list_queue, stretch=2)

        # Big "INICIAR CONVERSIÓN" Button
        self.btn_start = QPushButton("🚀 INICIAR CONVERSIÓN")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #FF9F0A;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #D68000;
            }
        """)
        self.btn_start.clicked.connect(self._iniciar_conversion)
        top_layout.addWidget(self.btn_start)

        main_layout.addWidget(self.top_card, stretch=3)

        # BOTTOM CARD BLOCK: Conversion & System Settings
        self.bottom_card = QFrame()
        self.bottom_card.setObjectName("CardBlock")
        bottom_layout = QVBoxLayout(self.bottom_card)
        bottom_layout.setContentsMargins(12, 10, 12, 10)
        bottom_layout.setSpacing(6)

        lbl_set_title = QLabel("Configuración de Conversión")
        lbl_set_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #F2F2F7;")
        bottom_layout.addWidget(lbl_set_title)

        # Automatic FFmpeg Status
        ff_frame = QFrame()
        ff_frame.setStyleSheet("background-color: #252528; border-radius: 6px; padding: 4px;")
        ff_layout = QHBoxLayout(ff_frame)
        ff_layout.setContentsMargins(8, 2, 8, 2)
        lbl_ff = QLabel("FFmpeg: Automático (Detectado en carpeta)")
        lbl_ff.setStyleSheet("font-size: 10px; font-weight: bold; color: #30D158;")
        ff_layout.addWidget(lbl_ff)
        bottom_layout.addWidget(ff_frame)

        # Stems Selector (4S vs 6S)
        lbl_stems = QLabel("Cantidad de Instrumentos:")
        lbl_stems.setStyleSheet("font-size: 10px; color: #8E8E93;")
        bottom_layout.addWidget(lbl_stems)

        stems_layout = QHBoxLayout()
        self.rb_4s = QRadioButton("4 Inst. (4S)")
        self.rb_6s = QRadioButton("6 Inst. (6S)")
        self.rb_4s.setStyleSheet("color: white; font-size: 11px;")
        self.rb_6s.setStyleSheet("color: white; font-size: 11px;")

        current_model = self.config.get("model", "htdemucs")
        if "6s" in current_model:
            self.rb_6s.setChecked(True)
        else:
            self.rb_4s.setChecked(True)

        self.rb_4s.toggled.connect(self._on_model_toggled)
        self.rb_6s.toggled.connect(self._on_model_toggled)

        stems_layout.addWidget(self.rb_4s)
        stems_layout.addWidget(self.rb_6s)
        bottom_layout.addLayout(stems_layout)

        # Hardware Device Selector (CPU vs CUDA)
        lbl_dev = QLabel("Procesamiento (Hardware):")
        lbl_dev.setStyleSheet("font-size: 10px; color: #8E8E93;")
        bottom_layout.addWidget(lbl_dev)

        dev_layout = QHBoxLayout()
        self.rb_cpu = QRadioButton("CPU")
        self.rb_cuda = QRadioButton("CUDA (NVIDIA GPU)")
        self.rb_cpu.setStyleSheet("color: white; font-size: 11px;")
        self.rb_cuda.setStyleSheet("color: white; font-size: 11px;")

        current_dev = self.config.get("device", "cpu")
        if current_dev == "cuda":
            self.rb_cuda.setChecked(True)
        else:
            self.rb_cpu.setChecked(True)

        self.rb_cpu.toggled.connect(self._on_device_toggled)
        self.rb_cuda.toggled.connect(self._on_device_toggled)

        dev_layout.addWidget(self.rb_cpu)
        dev_layout.addWidget(self.rb_cuda)
        bottom_layout.addLayout(dev_layout)

        main_layout.addWidget(self.bottom_card, stretch=1)

    def _agregar_carpeta(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de música")
        if folder_path:
            self.lbl_scan_status.setText("⏳ Escaneando carpeta en segundo plano...")
            existing_paths = {s["path"] for s in self.songs_data}
            self.scan_thread = FolderScannerThread(folder_path, existing_paths)
            self.scan_thread.song_found.connect(self._on_song_found)
            self.scan_thread.finished_scan.connect(self._on_scan_finished)
            self.scan_thread.start()

    def _on_song_found(self, meta):
        self.songs_data.append(meta)
        artist = meta["artist"]

        if artist not in self.artist_items:
            artist_node = QTreeWidgetItem(self.tree_songs)
            artist_node.setText(0, f"👤 {artist}")
            artist_node.setExpanded(True)
            artist_node.setFlags(artist_node.flags() & ~Qt.ItemIsSelectable)
            self.artist_items[artist] = artist_node

        song_node = QTreeWidgetItem(self.artist_items[artist])
        song_node.setText(0, f"🎵 {meta['title']}")
        song_node.setData(0, Qt.UserRole, meta)

    def _on_scan_finished(self, count):
        self.lbl_scan_status.setText(f"✅ {count} canciones agregadas")

    def _agregar_archivos(self):
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar canciones", "", "Audio (*.mp3 *.wav *.flac *.m4a *.aac *.ogg)")
        if rutas:
            for r in rutas:
                if not any(s["path"] == r for s in self.songs_data):
                    meta = get_song_metadata(r)
                    meta["path"] = r
                    self._on_song_found(meta)

    def _on_item_clicked(self, item, column):
        meta = item.data(0, Qt.UserRole)
        if meta:
            self.selected_song_meta = meta
            self.btn_listen_solo.setEnabled(True)
            self.btn_queue_add.setEnabled(True)
            self.song_selected.emit(meta, "single_preview")

    def _escuchar_sola(self):
        if self.selected_song_meta:
            self.song_selected.emit(self.selected_song_meta, "single_play")

    def _anadir_a_cola(self):
        if self.selected_song_meta:
            self.separator.add_to_queue([self.selected_song_meta["path"]])
            self.update_queue_status()

    def _iniciar_conversion(self):
        if self.separator.get_queue_size() == 0 and self.songs_data:
            all_paths = [s["path"] for s in self.songs_data]
            self.separator.add_to_queue(all_paths)

        self.separator.start_processing()
        self.update_queue_status()

    def update_queue_status(self):
        self.list_queue.clear()
        pending = list(self.separator.pending_list)
        current = self.separator.current_item

        total = len(pending) + (1 if current else 0)
        self.lbl_queue_title.setText(f"📋 Cola de Conversión ({total})")

        if current:
            item = QListWidgetItem(f"⚙️ Separando: {current}")
            item.setForeground(Qt.GlobalColor.yellow)
            self.list_queue.addItem(item)

        for p in pending:
            name = os.path.splitext(os.path.basename(p))[0]
            item = QListWidgetItem(f"⏳ En espera: {name}")
            self.list_queue.addItem(item)

    def _on_model_toggled(self):
        model_name = "htdemucs_6s" if self.rb_6s.isChecked() else "htdemucs"
        self.config.set("model", model_name)
        self.model_changed.emit(model_name)

    def _on_device_toggled(self):
        dev = "cuda" if self.rb_cuda.isChecked() else "cpu"
        self.config.set("device", dev)
