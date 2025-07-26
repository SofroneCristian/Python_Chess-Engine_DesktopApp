from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QSlider, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from game_window import GameWindow

class GameModeDialog(QDialog):
    # Constante pentru configurare
    WINDOW_SIZE = (400, 600)
    FONT_SIZE = {
        "normal": 12,
        "large": 14
    }
    
    STYLES = {
        "button": """
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                margin: 5px;
                border-radius: 8px;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1abc9c;
            }
            QPushButton[selected="true"] {
                background-color: #1abc9c;
                border: 2px solid #fff;
                font-weight: bold;
            }
        """,
        "start_button": """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                margin: 5px;
                border-radius: 8px;
                min-width: 250px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #219f56;
            }
        """
    }
    
    GAME_MODES = [
        ("Model as White vs Stockfish", True),
        ("Model as Black vs Stockfish", True),
        ("Model as White vs Player", False),
        ("Model as Black vs Player", False),
        ("Model vs Model", False),
        ("Player vs Player", False)
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Game Mode")
        self.setMinimumSize(*self.WINDOW_SIZE)
        
        self.stockfish_level = 0
        self.selected_mode = None
        self.game_window = None
        self.buttons = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        #Configurare UI
        layout = QVBoxLayout(self)
        
        self._setup_mode_buttons(layout)
        self._setup_stockfish_controls(layout)
        self._setup_control_buttons(layout)
    
    def _setup_mode_buttons(self, layout):
        for mode_text, has_stockfish in self.GAME_MODES:
            btn = QPushButton(mode_text)
            btn.setStyleSheet(self.STYLES["button"])
            btn.setFont(QFont("Arial", self.FONT_SIZE["normal"]))
            btn.clicked.connect(lambda checked, m=mode_text: self.on_mode_selected(m))
            self.buttons.append((btn, has_stockfish))
            layout.addWidget(btn)
    
    def _setup_stockfish_controls(self, layout):
        #Configurare slider nivel Stockfish
        self.slider_container = QWidget()
        slider_layout = QVBoxLayout(self.slider_container)
        
        self.level_label = QLabel("Stockfish Level: 0")
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_label.setFont(QFont("Arial", self.FONT_SIZE["normal"]))
        slider_layout.addWidget(self.level_label)
        
        self.level_slider = self._create_stockfish_slider()
        slider_layout.addWidget(self.level_slider)
        
        self.slider_container.hide()
        layout.addWidget(self.slider_container)
    
    def _create_stockfish_slider(self):
        #Creaaza slider-ul daca este cazul
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(20)
        slider.setValue(0)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(1)
        slider.valueChanged.connect(self.on_slider_changed)
        return slider
    
    def _setup_control_buttons(self, layout):
        self.start_button = QPushButton("Start Game")
        self.start_button.setStyleSheet(self.STYLES["start_button"])
        self.start_button.setFont(QFont("Arial", self.FONT_SIZE["large"], QFont.Weight.Bold))
        self.start_button.clicked.connect(self.accept)
        self.start_button.hide()
        layout.addWidget(self.start_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(self.STYLES["button"])
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
    
    def on_mode_selected(self, mode):
        #Handler pt Selectarea modului
        self.selected_mode = mode
        self._update_button_states(mode)
        self.start_button.show()
    
    def _update_button_states(self, selected_mode):
        #Selectarea butoanelor
        for btn, has_stockfish in self.buttons:
            is_selected = btn.text() == selected_mode
            btn.setProperty("selected", str(is_selected).lower())
            btn.setStyleSheet(btn.styleSheet())
            
            if btn.text() == selected_mode:
                self.slider_container.setVisible(has_stockfish)
                if not has_stockfish:
                    self.stockfish_level = 0
    
    def on_slider_changed(self, value):
        #Schimbarea sliderului
        self.level_label.setText(f"Stockfish Level: {value}")
        self.stockfish_level = value
    
    def accept(self):
        #Handler pentru inceperea jocului
        self.game_window = GameWindow(self.selected_mode, self.stockfish_level)
        self.game_window.show()
        self.parent().hide()
        self.game_window.closed.connect(self.on_game_window_closed)
        super().accept()
    
    def on_game_window_closed(self):
        self.parent().show()
        self.game_window = None 