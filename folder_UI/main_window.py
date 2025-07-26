from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QGraphicsOpacityEffect, QSizePolicy, QDialog)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QFont
from game_mode_dialog import GameModeDialog
from game_history_window import GameHistoryWindow


class MainWindow(QMainWindow):
    # Constante pentru configurare
    WINDOW_MIN_SIZE = (1024, 768)
    SLIDESHOW_INTERVAL = 5000  # ms
    FADE_DURATION = 1000  # ms
    BUTTON_FONT_SIZE = 14

    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IMAGES = [
        os.path.normpath(os.path.join(BASE_DIR, "..", "Utils", "Pictures", "imagine1.jpg")),
        os.path.normpath(os.path.join(BASE_DIR, "..", "Utils", "Pictures", "imagine2.jpg")),
        os.path.normpath(os.path.join(BASE_DIR, "..", "Utils", "Pictures", "imagine3.jpg")),
        os.path.normpath(os.path.join(BASE_DIR, "..", "Utils", "Pictures", "imagine4.jpg")),
    ]

    BUTTON_STYLE = """
        QPushButton {
            background-color: #2c3e50;
            color: white;
            border: none;
            padding: 15px 32px;
            font-size: 16px;
            margin: 10px;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #34495e;
        }
        QPushButton:pressed {
            background-color: #1abc9c;
        }
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Engine")
        self.setMinimumSize(*self.WINDOW_MIN_SIZE)
        
        self.game_dialog = None
        self.current_image = 0
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._setup_slideshow(layout)
        self._setup_buttons(layout)
        
        self.resizeEvent = self.on_resize
    
    def _setup_slideshow(self, layout):
        #Configuram Slideshow imagini
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setStyleSheet("QLabel { background-color: black; }")
        
        # Efect Fade la schimbarea imaginilor
        self.opacity_effect = QGraphicsOpacityEffect(self.image_label)
        self.image_label.setGraphicsEffect(self.opacity_effect)
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(self.FADE_DURATION)
        
        # Timer Schimbare imagini
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_image)
        self.timer.start(self.SLIDESHOW_INTERVAL)
        
        layout.addWidget(self.image_label)
    
    def _setup_buttons(self, main_layout):
        #Configurare Butoane Principale
        button_container = QWidget()
        button_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(20, 20, 20, 20)
        
        buttons = {
            "Play Game": self.on_play_clicked,
            "Game History": self.on_history_clicked
        }
        
        for text, handler in buttons.items():
            btn = QPushButton(text)
            btn.setStyleSheet(self.BUTTON_STYLE)
            btn.setFont(QFont("Arial", self.BUTTON_FONT_SIZE, QFont.Weight.Bold))
            btn.clicked.connect(handler)
            button_layout.addWidget(btn)
        
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(button_container)
    
    def show_image(self):
        #Afiseaza imaginea
        pixmap = QPixmap(self.IMAGES[self.current_image])
        scaled_pixmap = pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        if scaled_pixmap.width() > self.width() or scaled_pixmap.height() > self.height():
            x = (scaled_pixmap.width() - self.width()) // 2
            y = (scaled_pixmap.height() - self.height()) // 2
            scaled_pixmap = scaled_pixmap.copy(x, y, self.width(), self.height())
        
        self.image_label.setPixmap(scaled_pixmap)
        
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
    
    def next_image(self):
        self.current_image = (self.current_image + 1) % len(self.IMAGES)
        self.show_image()
    
    def on_play_clicked(self):
        #Handler buton play
        self.game_dialog = GameModeDialog(self)
        if self.game_dialog.exec() == QDialog.DialogCode.Accepted:
            print(f"Selected mode: {self.game_dialog.selected_mode}")
            print(f"Stockfish level: {self.game_dialog.stockfish_level}")
    
    def on_history_clicked(self):
        #Handler buton istoric
        self.history_window = GameHistoryWindow(self)
        self.history_window.show()
    
    def on_resize(self, event):
        #Handler redimensionare
        super().resizeEvent(event)
        self.show_image()