from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QFont
from PyQt6.QtCore import Qt, QRectF
from stockFishBot import StockfishBot
import math

class EvaluationBarWidget(QWidget):
    # Constante
    COLORS = {
        "white": QColor("#FFFFFF"),
        "black": QColor("#4D4D4D"),
        "border": QColor("#2c3e50"),
        "text_white": QColor("#FFFFFF"),
        "text_black": QColor("#000000")
    }
    
    BAR_WIDTH = 30
    SIGMOID_FACTOR = 400  # Factor normalizare evaluare
    BORDER_WIDTH = 1
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.BAR_WIDTH)
        self.evaluation = 0
        self.stockfish = StockfishBot(level=20)
        self.font = QFont("Arial", 8, QFont.Weight.Bold)
        
    def update_evaluation(self, board):
        eval = self.stockfish.get_evaluation(board) or 0
        self.evaluation = -eval if not board.board.turn else eval
        self.update()
    
    def _normalize_evaluation(self):
        return 2 / (1 + math.exp(-self.evaluation/self.SIGMOID_FACTOR)) - 1
    
    def _create_gradient(self, start_y, height, is_white):
        gradient = QLinearGradient(0, start_y, 0, start_y + height)
        
        color = self.COLORS["white"] if is_white else self.COLORS["black"]
        color_transparent = QColor(color)
        color_transparent.setAlpha(180)
        
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, color_transparent)
        
        return gradient
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setFont(self.font)
        
        # Dimensiuni
        center_y = self.height() // 2
        normalized = self._normalize_evaluation()
        bar_height = int(self.height() * abs(normalized))
        
        painter.fillRect(0, 0, self.width(), center_y, self.COLORS["black"])
        painter.fillRect(0, center_y, self.width(), center_y, self.COLORS["white"])
        
        if self.evaluation > 0:  
            start_y = center_y - bar_height
            gradient = self._create_gradient(start_y, bar_height, True)
            painter.fillRect(0, start_y, self.width(), bar_height, gradient)
        else:  
            gradient = self._create_gradient(center_y, bar_height, False)
            painter.fillRect(0, center_y, self.width(), bar_height, gradient)
        
        # Centrul Evaluarii
        pen = QPen(self.COLORS["border"], self.BORDER_WIDTH)
        painter.setPen(pen)
        painter.drawLine(0, center_y, self.width(), center_y)
        
        # Afisam evaluarea numerica
        eval_text = f"{abs(self.evaluation/100):.1f}"
        text_color = self.COLORS["text_white"] if self.evaluation < 0 else self.COLORS["text_black"]
        painter.setPen(text_color)
        
        # Dreptunghi pentru text
        text_rect = QRectF(0, 0, self.width(), self.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, eval_text)
    
    def cleanup(self):
        #Inchidem Stockfish
        self.stockfish.close() 