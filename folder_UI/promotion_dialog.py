from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtSvg import QSvgRenderer
import os

class PromotionDialog(QDialog):
    PIECES = {
        'q': 'queen',
        'r': 'rook',
        'n': 'knight',
        'b': 'bishop'
    }
    
    BUTTON_STYLE = """
        QPushButton {
            min-width: 60px;
            min-height: 60px;
            margin: 5px;
            border: 2px solid #666;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #eee;
        }
    """
    
    def __init__(self, parent=None, is_white=True):
        super().__init__(parent)
        self.setWindowTitle("Alege piesa pentru promovare")
        self.setStyleSheet(self.BUTTON_STYLE)
        
        self.selected_piece = None
        self._setup_ui(is_white)
    
    def _setup_ui(self, is_white):
        #Configurare Interfata
        layout = QVBoxLayout()
        color = 'w' if is_white else 'b'
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder_UI/
        PIECE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "Utils", "Chess_pieces"))
        
        for piece, name in self.PIECES.items():
            btn = QPushButton()
            icon_path = os.path.join(PIECE_DIR, f"{color}_{name}_svg_NoShadow.svg")
            self._setup_button(btn, icon_path, piece)
            layout.addWidget(btn)
        
        self.setLayout(layout)
    
    def _setup_button(self, button, icon_path, piece):
        #Buton pentru o piesa
        renderer = QSvgRenderer(icon_path)
        pixmap = QPixmap(60, 60)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        button.setIcon(QIcon(pixmap))
        button.setIconSize(QSize(50, 50))
        button.clicked.connect(lambda checked, p=piece: self.select_piece(p))
    
    def select_piece(self, piece):
        #Handler pentru selectarea piesei
        self.selected_piece = piece
        self.accept() 