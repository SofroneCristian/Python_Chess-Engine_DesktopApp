from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog, QVBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPixmap, QIcon
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal
from PyQt6.QtSvg import QSvgRenderer
import chess
import os
from board import ChessBoard
from promotion_dialog import PromotionDialog  

class ChessBoardWidget(QWidget):
    move_made = pyqtSignal()
    
    # Constante pentru configurare
    SQUARE_COLORS = {
        "light": QColor("#F0D9B5"),
        "dark": QColor("#B58863"),
        "check": QColor("#FF6B6B")
    }
    
    PIECE_SCALE = 0.8  
    HOVER_OFFSET = 10  # Offset-ul piesa selectata
    
    PIECE_TYPES = {
        'p': 'pawn',
        'r': 'rook',
        'n': 'knight',
        'b': 'bishop',
        'q': 'queen',
        'k': 'king'
    }
    
    def __init__(self, reversed_board=False, game_mode=None):
        super().__init__()
        self.reversed_board = reversed_board
        self.game_mode = game_mode
        
        self.board = ChessBoard()
        self.selected_piece = None
        self.possible_moves = []
        
        self._setup_board_coordinates()
        self._setup_ui()
        self.load_pieces()
        self.initial_position = self.get_initial_position()
        
        self.setMouseTracking(True)
    
    def _setup_board_coordinates(self):
        self.files = 'abcdefgh'
        self.ranks = '12345678'
    
    def _setup_ui(self):
        self.setMinimumSize(400, 400)
    
    def load_pieces(self):
        self.pieces = {}
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder_UI/
        PIECE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "Utils", "Chess_pieces"))
        for piece, name in self.PIECE_TYPES.items():
            white_path = os.path.join(PIECE_DIR, f"w_{name}_svg_NoShadow.svg")
            black_path = os.path.join(PIECE_DIR, f"b_{name}_svg_NoShadow.svg")

            self.pieces[piece.upper()] = QSvgRenderer(white_path)
            self.pieces[piece] = QSvgRenderer(black_path)
    
    def get_initial_position(self):
        #Convertim pozitia din python-chess in reprezentarea noastra + inverseaza daca este cazul
        position = []
        board_str = str(self.board.board)  
        lines = board_str.split('\n')
        
        for line in lines:
            row = []
            for i in range(0, len(line), 2):  
                piece = line[i]
                row.append(piece if piece != '.' else '.')
            position.append(row)
        
        if self.reversed_board:
            position = list(reversed([row[::-1] for row in position]))
        
        return position
    
    def get_square_notation(self, col, row):
        #convertim din matrice in notatie UCI
        if self.reversed_board:
            file_idx = 7 - col  
            rank_idx = row      
        else:
            file_idx = col
            rank_idx = 7 - row
        return f"{self.files[file_idx]}{self.ranks[rank_idx]}"
    
    def is_promotion_move(self, from_row, to_row, piece):
        if self.reversed_board:
            return (piece == 'P' and to_row == 7) or (piece == 'p' and to_row == 0)
        return (piece == 'P' and to_row == 0) or (piece == 'p' and to_row == 7)
    
    
    def calculate_possible_moves(self, from_square):
        #Calculam toate mutarile posibile pentru o piesa
        moves = []
        for move in self.board.board.legal_moves:
            if chess.square_name(move.from_square) == from_square:
                to_square = chess.square_name(move.to_square)
                file_idx = self.files.index(to_square[0])
                rank_idx = self.ranks.index(to_square[1])
                
                display_row = 7 - rank_idx if not self.reversed_board else rank_idx
                display_col = file_idx if not self.reversed_board else 7 - file_idx
                moves.append((display_row, display_col))
        return moves
    
    def _is_move_allowed(self):
        #Verifica daca mutarile de la tastatura sunt permise
        if not self.game_mode:
            return True
        
        if self.game_mode == "history" or "Model vs Model" in self.game_mode:
            return False
        
        if "Model as White vs Player" in self.game_mode:
            return not self.board.board.turn  
        if "Model as Black vs Player" in self.game_mode:
            return self.board.board.turn  
        
        return True
    
    def mousePressEvent(self, event):
        if not self._is_move_allowed() or event.button() != Qt.MouseButton.LeftButton:
            return
            
        square_size = min(self.width(), self.height()) // 8
        col = int(event.position().x() // square_size)
        row = int(event.position().y() // square_size)
        
        if self.selected_piece and (row, col) in self.possible_moves:
            self._handle_move(row, col)
        else:
            self._handle_piece_selection(row, col)
    
    def _handle_move(self, row, col):
        #Gestioneaza mutarea efectiva a piesei
        from_col = self.selected_piece[1]
        from_row = self.selected_piece[0]
        
        from_square = self.get_square_notation(from_col, from_row)
        to_square = self.get_square_notation(col, row)
        
        piece = self.initial_position[from_row][from_col]
        move = None
        
        if self.is_promotion_move(from_row, row, piece):
            move = self._handle_promotion(from_square, to_square, piece.isupper())
            if not move:
                return
        else:
            move = chess.Move.from_uci(from_square + to_square)
        
        if move and move in self.board.board.legal_moves:
            self._execute_move(move)
    
    def _handle_promotion(self, from_square, to_square, is_white):
        #Gestioneaza promovarea pionului
        dialog = PromotionDialog(self, is_white)
        if dialog.exec():
            promotion_piece = dialog.selected_piece
            return chess.Move.from_uci(from_square + to_square + promotion_piece)
        return None
    
    def _execute_move(self, move):
        #Executa Miscarea si updateaza starea jocului
        old_board = str(self.board.board)
        
        if hasattr(self.parent(), 'game_manager'):
            self._update_game_manager_stats(move)
        
        # Facem mutarea
        self.board.make_move(move.uci(), self.board.current_player)
        if hasattr(self.parent(), 'game_manager'):
            self.parent().game_manager.board = self.board
        
        # Actualizăm tabla
        new_board = str(self.board.board)
        self.initial_position = self.get_initial_position()
        self.update_visual_board(old_board, new_board)
        
        # Verificăm pentru final de joc
        self._check_game_end()
        
        # Resetăm selecția
        self.selected_piece = None
        self.possible_moves = []
        self.update()
        
        # Emitem semnalul
        self.move_made.emit()
    
    def _update_game_manager_stats(self, move):
        #Actualizeaza statisticile din game_manager
        gm = self.parent().game_manager
        gm.game_moves.append(move.uci())
        gm.stats["numar_miscari"] += 1
        
        if self.board.board.is_capture(move):
            gm.stats["capturi"] += 1
        if self.board.board.gives_check(move):
            gm.stats["sahuri"] += 1
    
    def _check_game_end(self):
        #Verifica daca s a terminat + afiseaza mesaj+ apeleaza salvarea
        if self.board.board.is_checkmate():
            winner = "Negru" if self.board.board.turn else "Alb"
            QMessageBox.information(self, "Șah Mat!", f"Jocul s-a terminat! {winner} a câștigat!")
            if hasattr(self.parent(), 'game_manager'):
                self.parent().game_manager.save_game()
        elif self.board.board.is_stalemate():
            QMessageBox.information(self, "Remiză!", "Jocul s-a terminat! Este pat!")
            if hasattr(self.parent(), 'game_manager'):
                self.parent().game_manager.save_game()
    
    def paintEvent(self, event):
        #Metoda standard, ce este apelata automat pentru a redesena interfata grafica
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        square_size = min(self.width(), self.height()) // 8
        
        self.draw_board(painter, square_size)
        self.draw_possible_moves(painter, square_size)
        self.draw_pieces(painter, square_size)
    
    def draw_board(self, painter, square_size):
        #Deseneaza Tabla de Sah
        for row in range(8):
            for col in range(8):
                x = col * square_size
                y = row * square_size
                
                # Culoarea normală a pătrățelului
                color = self.SQUARE_COLORS["light"] if (row + col) % 2 == 0 else self.SQUARE_COLORS["dark"]
                
                # Verificăm dacă regele este în șah și colorăm pătrățelul
                if self.board.board.is_check():
                    king_color = self.board.board.turn  # True pentru alb, False pentru negru
                    king_square = self.board.board.king(king_color)
                    king_file = chess.square_file(king_square)
                    king_rank = chess.square_rank(king_square)
                    
                    # Convertim coordonatele pentru afișare
                    if not self.reversed_board:
                        display_row = 7 - king_rank
                        display_col = king_file
                    else:
                        display_row = king_rank
                        display_col = 7 - king_file
                    
                    if row == display_row and col == display_col:
                        color = self.SQUARE_COLORS["check"]  # Roșu pentru șah
                
                painter.fillRect(x, y, square_size, square_size, color)
    
    def draw_possible_moves(self, painter, square_size):
        #Afiseaza mutarile posibile
        if self.possible_moves:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 127))
            
            for row, col in self.possible_moves:
                x = col * square_size
                y = row * square_size
                center_x = x + square_size // 2
                center_y = y + square_size // 2
                radius = square_size // 6
                painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
    
    def draw_pieces(self, painter, square_size):
        #Pozitia Initiala a pieselor
        for row in range(8):
            for col in range(8):
                piece = self.initial_position[row][col]
                if piece != '.':
                    x = col * square_size
                    y = row * square_size
                    self.draw_piece(painter, piece, x, y, square_size)
    
    def draw_piece(self, painter, piece, x, y, size):
        #Deseneaza o piesa
        if piece in self.pieces:
            piece_size = int(size * self.PIECE_SCALE)
            x_offset = (size - piece_size) // 2
            y_offset = (size - piece_size) // 2
            
            # Aplicăm offset dacă piesa e selectată
            if self.selected_piece and \
               (y // size) == self.selected_piece[0] and \
               (x // size) == self.selected_piece[1]:
                y_offset -= self.HOVER_OFFSET
            
            rect = QRectF(x + x_offset, y + y_offset, piece_size, piece_size)
            self.pieces[piece].render(painter, rect)
    
    def update_visual_board(self, old_board, new_board):
        #Actualizeaza Reprezentarea Vizuala a Tablei
        old_lines = old_board.split('\n')
        new_lines = new_board.split('\n')
        
        for i in range(8):
            for j in range(8):
                old_piece = old_lines[i][j*2]
                new_piece = new_lines[i][j*2]
                
                if old_piece != new_piece:
                    row = i if not self.reversed_board else 7-i
                    col = j if not self.reversed_board else 7-j
                    
                    # Convertim piesele din formatul FEN în formatul nostru
                    piece_map = {
                        'P': 'P', 'p': 'p',
                        'R': 'R', 'r': 'r',
                        'N': 'N', 'n': 'n',
                        'B': 'B', 'b': 'b',
                        'Q': 'Q', 'q': 'q',
                        'K': 'K', 'k': 'k',
                        '.': '.'
                    }
                    self.initial_position[row][col] = piece_map.get(new_piece, '.') 
    
    def _handle_piece_selection(self, row, col):
        #Handler pentru selectarea pieselor
        square_name = self.get_square_notation(col, row)
        square = chess.parse_square(square_name)
        piece = self.board.board.piece_at(square)
        
        # Verificăm dacă există o piesă și dacă e rândul ei
        if piece and piece.color == self.board.board.turn:
            self.selected_piece = (row, col)
            self.possible_moves = self.calculate_possible_moves(square_name)
        else:
            self.selected_piece = None
            self.possible_moves = []
        
        self.update() 