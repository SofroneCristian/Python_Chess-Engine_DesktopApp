from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import pyqtSignal, QTimer
from chess_board_widget import ChessBoardWidget
from chess_models.chess_ai import ChessAI
from stockFishBot import StockfishBot
from runGame import GameManager
import chess

class GameWindow(QMainWindow):
    closed = pyqtSignal()
    
    def __init__(self, game_mode, stockfish_level=0):
        super().__init__()
        self.setWindowTitle("Chess Game")
        self.setMinimumSize(800, 600)
        
        self.game_mode = game_mode
        self.auto_play = False
        
        # Inițializare GameManager
        self.game_manager = GameManager()
        self._setup_game_manager(game_mode, stockfish_level)
        
        # Inițializare modele
        if "Model" in game_mode:
            self.model = ChessAI()
        if "Stockfish" in game_mode:
            self.stockfish = StockfishBot(level=stockfish_level)
        
        # Setup UI
        self._setup_ui(game_mode)
        
        # Dacă modelul începe cu albele, facem prima mutare
        if "Model as White" in game_mode:
            QTimer.singleShot(500, self.make_model_move)
    
    def _setup_game_manager(self, game_mode, stockfish_level):
        #Pentru Setup-ul jucatorilor din Game Manager
        if "Model as White vs Player" in game_mode:
            self.game_manager.setup_game('model', 'human')
        elif "Model as Black vs Player" in game_mode:
            self.game_manager.setup_game('human', 'model')
        elif "Model as White vs Stockfish" in game_mode:
            self.game_manager.setup_game('model', 'stockfish', stockfish_level)
        elif "Model as Black vs Stockfish" in game_mode:
            self.game_manager.setup_game('stockfish', 'model', stockfish_level)
        elif "Model vs Model" in game_mode:
            self.game_manager.setup_game('model', 'model')
        else:  
            self.game_manager.setup_game('human', 'human')  
    
    def _setup_ui(self, game_mode):
        #Interfata Utilizator
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        #Inversam tabela 
        reversed_board = "Model as White vs Player" in game_mode
        
        # Adaugam widget-ul tablei 
        self.chess_board = ChessBoardWidget(reversed_board=reversed_board, game_mode=game_mode)
        main_layout.addWidget(self.chess_board)
        
        # Adaugam butoanele pt joc automat
        if ("Model" in game_mode and "Stockfish" in game_mode) or game_mode == "Model vs Model":
            self._add_control_buttons(main_layout)
        
        # Conectam semnalele cand jucam noi
        if "vs Player" in game_mode:
            self.chess_board.move_made.connect(self.on_player_move)
        self.chess_board.move_made.connect(self.on_move_made)
    
    def _add_control_buttons(self, main_layout):
        #Butoane de control pentru jocurile intre boti
        button_layout = QHBoxLayout()
        
        self.next_move_btn = QPushButton("Următoarea mutare")
        self.next_move_btn.clicked.connect(self.make_next_move)
        button_layout.addWidget(self.next_move_btn)
        
        self.auto_play_btn = QPushButton("Auto Play")
        self.auto_play_btn.setCheckable(True)
        self.auto_play_btn.clicked.connect(self.toggle_auto_play)
        button_layout.addWidget(self.auto_play_btn)
        
        main_layout.addLayout(button_layout)
    
    def update_stats(self, move):
        #Actualizare statistici
        self.game_manager.game_moves.append(move.uci())
        self.game_manager.stats["numar_miscari"] += 1
        
        if self.chess_board.board.board.is_capture(move):
            self.game_manager.stats["capturi"] += 1
        
        if self.chess_board.board.board.is_check():
            self.game_manager.stats["sahuri"] += 1
    
    def execute_move(self, move):
        old_board = str(self.chess_board.board.board)
        self.chess_board.board.make_move(move.uci(), self.chess_board.board.current_player)
        self.game_manager.board = self.chess_board.board
        new_board = str(self.chess_board.board.board)
        self.chess_board.update_visual_board(old_board, new_board)
    
    def disable_controls(self):
        #Dezactivam controalele dupa terminarea jocului
        self.auto_play = False
        if hasattr(self, 'auto_play_btn'):
            self.auto_play_btn.setChecked(False)
            self.auto_play_btn.setEnabled(False)
        if hasattr(self, 'next_move_btn'):
            self.next_move_btn.setEnabled(False)
    
    def on_player_move(self):
        #handler pentru mutarile jucatorului
        if "vs Player" in self.game_mode:
            last_move = self.chess_board.board.board.peek()
            self.update_stats(last_move)
            self.check_game_over()
    
    def on_move_made(self):
        #Handle pentru cand se face o mutare pe tabla
        if "Model" in self.game_mode and "vs Player" in self.game_mode:
            QTimer.singleShot(500, self.make_model_move)
    
    def make_model_move(self):
        move = self.model.get_best_move(self.chess_board.board)
        if move:
            self.update_stats(move)
            self.execute_move(move)
            if not self.check_game_over() and self.auto_play:
                QTimer.singleShot(100, self.make_next_move)
            
            self.chess_board.update()
    
    def make_next_move(self):
        #Mutarile in modurile automate
        if self.chess_board.board.board.is_game_over():
            self.check_game_over()
            return
        
        is_whites_turn = self.chess_board.board.board.turn
        
        if self.game_mode == "Model vs Model":
            move = self.model.get_best_move(self.chess_board.board)
        else:
            is_model_white = "Model as White" in self.game_mode
            if is_whites_turn == is_model_white:
                move = self.model.get_best_move(self.chess_board.board)
            else:
                move = self.stockfish.get_best_move(self.chess_board.board)
        
        if move:
            self.update_stats(move)
            self.execute_move(move)
            
            if not self.check_game_over() and self.auto_play:
                QTimer.singleShot(100, self.make_next_move)
            
            self.chess_board.update()
    
    def check_game_over(self):
        #Verifica daca s a terminat jocul
        board = self.chess_board.board.board
        
        if board.is_fivefold_repetition():
            QMessageBox.information(self.chess_board, "Remiză!", "Jocul s-a terminat! Remiză prin repetiție de 5 ori!")
            self.game_manager.stats["scor"] = "1/2-1/2"
            self.disable_controls()
            self.game_manager.save_game()
            return True
        
        outcome = board.outcome(claim_draw=False)
        if outcome is not None:
            if outcome.winner is not None:
                winner = "Negru" if outcome.winner == chess.BLACK else "Alb"
                QMessageBox.information(self.chess_board, "Șah Mat!", f"Jocul s-a terminat! {winner} a câștigat!")
                self.game_manager.stats["scor"] = "0-1" if outcome.winner == chess.BLACK else "1-0"
            else:
                reason = {
                    chess.Termination.STALEMATE: "Remiza prin Stalemate!",
                    chess.Termination.INSUFFICIENT_MATERIAL: "Remiză prin material insuficient!",
                    chess.Termination.FIFTY_MOVES: "Remiză prin regula 50 de mutări!",
                    chess.Termination.FIVEFOLD_REPETITION: "Remiză prin repetiție de 5 ori!",
                    chess.Termination.SEVENTYFIVE_MOVES: "Remiză prin regula 75 de mutări!"
                }.get(outcome.termination, "Remiză!")
                
                QMessageBox.information(self.chess_board, "Remiză!", f"Jocul s-a terminat! {reason}")
                self.game_manager.stats["scor"] = "1/2-1/2"
            
            self.disable_controls()
            self.game_manager.save_game()
            return True
        
        return False
    
    def toggle_auto_play(self, checked):
        self.auto_play = checked
        if checked:
            self.make_next_move()
    
    def closeEvent(self, event):
        if hasattr(self, 'stockfish'):
            self.stockfish.close()
        self.closed.emit()
        super().closeEvent(event) 