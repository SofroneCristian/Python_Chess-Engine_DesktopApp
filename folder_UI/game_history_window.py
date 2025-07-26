from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt
from chess_board_widget import ChessBoardWidget
from board import ChessBoard
import json
from evaluation_bar_widget import EvaluationBarWidget

class GameHistoryWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Istoric Jocuri")
        self.setMinimumSize(1200, 800)
        
        self.current_game_moves = []
        self.current_move_index = -1
        
        self._setup_ui()
        self._setup_button_style()
        self.load_games()
        self.update_controls()
    
    def _setup_ui(self):
        #Configuram Interfata Utilizator
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 3)
        
        #Lista si Butoanele
        left_layout = self._setup_left_panel()
        main_layout.addLayout(left_layout)
        
        #tabla si evaluarea
        board_layout = self._setup_board_panel()
        main_layout.addLayout(board_layout)
    
    def _setup_left_panel(self):
        #Configureaza panoul si butoanele
        left_layout = QVBoxLayout()
        
        # Listview
        self.games_list = QListWidget()
        self.games_list.itemClicked.connect(self.load_game)
        left_layout.addWidget(self.games_list)
        
        # Instantiere Butoane Control
        button_layout = QHBoxLayout()
        self._setup_control_buttons(button_layout)
        left_layout.addLayout(button_layout)
        
        self.delete_btn = QPushButton("Șterge jocul")
        self.delete_btn.clicked.connect(self.delete_game)
        self.delete_btn.setEnabled(False)
        left_layout.addWidget(self.delete_btn)
        
        return left_layout
    
    def _setup_control_buttons(self, layout):
        #Configurarea butoanelor de control
        self.start_btn = QPushButton("⏮")
        self.prev_btn = QPushButton("⏪")
        self.next_btn = QPushButton("⏩")
        self.end_btn = QPushButton("⏭")
        
        self.start_btn.clicked.connect(self.go_to_start)
        self.prev_btn.clicked.connect(self.prev_move)
        self.next_btn.clicked.connect(self.next_move)
        self.end_btn.clicked.connect(self.go_to_end)
        
        for btn in [self.start_btn, self.prev_btn, self.next_btn, self.end_btn]:
            layout.addWidget(btn)
    
    def _setup_board_panel(self):
        #Configurarea tablei si a evaluarii
        board_layout = QVBoxLayout()
        board_layout.setStretch(0, 9)
        board_layout.setStretch(1, 1)
        
        self.chess_board = ChessBoardWidget(game_mode="history")
        self.chess_board.setMinimumSize(600, 600)
        self.eval_bar = EvaluationBarWidget()
        
        board_layout.addWidget(self.chess_board)
        board_layout.addWidget(self.eval_bar)
        
        return board_layout
    
    def _setup_button_style(self):
        button_style = """
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """
        for btn in [self.start_btn, self.prev_btn, self.next_btn, self.end_btn]:
            btn.setStyleSheet(button_style)
    
    def _update_board_position(self, move):
        #Actualizarea tabelei.
        if move in [m.uci() for m in self.chess_board.board.board.legal_moves]:
            old_board = str(self.chess_board.board.board)
            self.chess_board.board.make_move(move, self.chess_board.board.current_player)
            new_board = str(self.chess_board.board.board)
            self.chess_board.initial_position = self.chess_board.get_initial_position()
            self.chess_board.update_visual_board(old_board, new_board)
    
    def load_games(self):
        #Incarcam in Json
        try:
            with open("Jocuri.json", "r") as f:
                games = json.load(f)
                for game in games:
                    item_text = (f"{game.get('game_mode', 'Joc necunoscut')}\n"
                               f"{game.get('castigator', 'necunoscut')} a câștigat\n"
                               f"Jucat la: {game.get('timestamp', 'Data necunoscută')}")
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, game)
                    self.games_list.addItem(item)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Nu s-au găsit jocuri salvate")
    
    def load_game(self, item):
        #Incarca un joc din LV
        self.delete_btn.setEnabled(True)
        game_data = item.data(Qt.ItemDataRole.UserRole)
        self.current_game_moves = game_data["mutari"]
        self.current_move_index = -1
        self.go_to_start()
    
    def next_move(self):
        if self.current_move_index + 1 < len(self.current_game_moves):
            self.current_move_index += 1
            move = self.current_game_moves[self.current_move_index]
            self._update_board_position(move)
            self.chess_board.update()
            self.eval_bar.update_evaluation(self.chess_board.board)
            self.update_controls()
    
    def prev_move(self):
        if self.current_move_index >= 0:
            self.chess_board.board = ChessBoard()
            self.chess_board.initial_position = self.chess_board.get_initial_position()
            self.current_move_index -= 1
            
            for i in range(self.current_move_index + 1):
                self._update_board_position(self.current_game_moves[i])
            
            self.chess_board.update()
            self.eval_bar.update_evaluation(self.chess_board.board)
            self.update_controls()
    
    def go_to_start(self):
        self.chess_board.board = ChessBoard()
        self.chess_board.initial_position = self.chess_board.get_initial_position()
        self.current_move_index = -1
        self.chess_board.update()
        self.update_controls()
    
    def go_to_end(self):
        self.go_to_start()
        for _ in range(len(self.current_game_moves)):
            self.next_move()
    
    def update_controls(self):
        #Actualizeaza starea butoanelor
        self.start_btn.setEnabled(self.current_move_index > -1)
        self.prev_btn.setEnabled(self.current_move_index > -1)
        self.next_btn.setEnabled(self.current_move_index + 1 < len(self.current_game_moves))
        self.end_btn.setEnabled(self.current_move_index + 1 < len(self.current_game_moves))
    
    def delete_game(self):
        current_item = self.games_list.currentItem()
        if current_item and self._confirm_delete():
            self._delete_game_from_json(current_item)
            self._update_ui_after_delete()
    
    def _confirm_delete(self):
        reply = QMessageBox.question(
            self, 'Confirmare',
            'Sigur vrei să ștergi acest joc?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    def _delete_game_from_json(self, item):
        with open("Jocuri.json", "r") as f:
            games = json.load(f)
        
        games.pop(self.games_list.row(item))
        
        with open("Jocuri.json", "w") as f:
            json.dump(games, f, indent=2)
    
    def _update_ui_after_delete(self):
        self.games_list.takeItem(self.games_list.currentRow())
        self.delete_btn.setEnabled(False)
        self.go_to_start()
    
    def closeEvent(self, event):
        self.eval_bar.cleanup()
        super().closeEvent(event) 