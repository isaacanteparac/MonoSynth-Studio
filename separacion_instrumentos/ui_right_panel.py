import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal

class RightPanel(QWidget):
    play_stems_requested = Signal(str, str, list) # (folder_path, song_name, stems_list)

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.selected_folder = None

        self._create_ui()
        self.refresh_divided_songs()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.card = QFrame()
        self.card.setObjectName("CardBlock")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        lbl_title = QLabel("Canciones Divididas")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #F2F2F7;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("background-color: #2C2C2E; color: white; border-radius: 6px; font-size: 10px; font-weight: bold; padding: 4px 8px;")
        btn_refresh.clicked.connect(self.refresh_divided_songs)
        header_layout.addWidget(btn_refresh)
        card_layout.addLayout(header_layout)

        lbl_root = QLabel("📁  monosync  (Carpeta Principal)")
        lbl_root.setStyleSheet("font-size: 12px; font-weight: bold; color: #30D158;")
        card_layout.addWidget(lbl_root)

        # Native Qt Tree Widget for divided songs hierarchy
        self.tree_divided = QTreeWidget()
        self.tree_divided.setHeaderHidden(True)
        self.tree_divided.setStyleSheet("""
            QTreeWidget {
                background-color: #121214;
                border: none;
                border-radius: 8px;
                color: #F2F2F7;
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
        self.tree_divided.itemClicked.connect(self._on_item_clicked)
        self.tree_divided.itemDoubleClicked.connect(self._cargar_mezclador)
        card_layout.addWidget(self.tree_divided, stretch=1)

        # Button to Load Stems
        self.btn_load_stems = QPushButton("🎛 Cargar Mezclador Stems")
        self.btn_load_stems.setEnabled(False)
        self.btn_load_stems.setCursor(Qt.PointingHandCursor)
        self.btn_load_stems.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0066CC;
            }
            QPushButton:disabled {
                background-color: #2C2C2E;
                color: #636366;
            }
        """)
        self.btn_load_stems.clicked.connect(self._cargar_mezclador)
        card_layout.addWidget(self.btn_load_stems)

        main_layout.addWidget(self.card)

    def refresh_divided_songs(self):
        self.tree_divided.clear()
        output_dir = self.config.get("output_dir", os.path.abspath("monosync"))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        items = os.listdir(output_dir)
        folders = [f for f in items if os.path.isdir(os.path.join(output_dir, f)) and not f.startswith("_")]

        if not folders:
            item = QTreeWidgetItem(self.tree_divided)
            item.setText(0, "No hay canciones divididas todavía.")
            item.setForeground(0, Qt.GlobalColor.gray)
            self.btn_load_stems.setEnabled(False)
            return

        for folder_name in folders:
            folder_path = os.path.join(output_dir, folder_name)
            folder_node = QTreeWidgetItem(self.tree_divided)
            folder_node.setText(0, f"📂  {folder_name}")
            folder_node.setData(0, Qt.UserRole, folder_path)
            folder_node.setExpanded(True)

            stems_found = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
            for s in stems_found:
                stem_node = QTreeWidgetItem(folder_node)
                stem_node.setText(0, f"└── 🎵 {s}")
                stem_node.setFlags(stem_node.flags() & ~Qt.ItemIsSelectable)

    def _on_item_clicked(self, item, column):
        folder_path = item.data(0, Qt.UserRole)
        if folder_path:
            self.selected_folder = folder_path
            self.btn_load_stems.setEnabled(True)

    def _cargar_mezclador(self):
        if self.selected_folder and os.path.exists(self.selected_folder):
            song_name = os.path.basename(self.selected_folder)
            stems_found = [f.replace(".wav", "").upper() for f in os.listdir(self.selected_folder) if f.endswith(".wav")]

            preferred_order = ["VOCALS", "DRUMS", "BASS", "PIANO", "GUITAR", "OTHER"]
            ordered_stems = [s for s in preferred_order if s in stems_found]
            for s in stems_found:
                if s not in ordered_stems:
                    ordered_stems.append(s)

            self.play_stems_requested.emit(self.selected_folder, song_name, ordered_stems)
