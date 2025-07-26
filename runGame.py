from board import ChessBoard
from chess_models.chess_ai import ChessAI
from stockFishBot import StockfishBot
import chess
import json
from datetime import datetime

class GameManager:
    def __init__(self):
        self.board = ChessBoard()
        self.game_moves = []
        self.stats = {
            "numar_miscari": 0,
            "capturi": 0,
            "sahuri": 0,
            "scor": ""
        }
        
    def setup_game(self, white_player_type: str, black_player_type: str, stockfish_level: int = 0):
        #Configuram Jocul
        self.white_player_type = white_player_type
        self.black_player_type = black_player_type
        self.stockfish_level = stockfish_level
        
        if 'stockfish' in (white_player_type, black_player_type):
            self.stockfish = StockfishBot(level=stockfish_level)
        if 'model' in (white_player_type, black_player_type):
            self.model = ChessAI()
    
    def save_game(self):
        #Salvam Jocul
        # Determinăm game mode-ul
        if self.white_player_type == 'model' and self.black_player_type == 'stockfish':
            game_mode = f"Model as White vs Stockfish level {self.stockfish_level}"
        elif self.white_player_type == 'stockfish' and self.black_player_type == 'model':
            game_mode = f"Model as Black vs Stockfish level {self.stockfish_level}"
        elif self.white_player_type == 'model' and self.black_player_type == 'model':
            game_mode = "Model vs Model"
        else:
            game_mode = f"{self.white_player_type} vs {self.black_player_type}"

        game_data = {
            "game_mode": game_mode,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "numar_miscari": self.stats["numar_miscari"],
            "capturi": self.stats["capturi"],
            "sahuri": self.stats["sahuri"],
            "castigator": self.determine_winner(),
            "scor": self.stats["scor"],
            "mutari": self.game_moves
        }

        try:
            with open("Jocuri.json", "r") as f:
                games = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            games = []

        games.append(game_data)

        with open("Jocuri.json", "w") as f:
            json.dump(games, f, indent=2)

    def determine_winner(self):
        if self.stats["scor"] == "1/2-1/2":
            return "draw"
            
        white_won = self.stats["scor"] == "1-0"
        
        if 'model' in (self.white_player_type, self.black_player_type) \
                and 'stockfish' in (self.white_player_type, self.black_player_type):
            return "model" if (
                (white_won and self.white_player_type == "model") or 
                (not white_won and self.black_player_type == "model")
            ) else "stockfish"
        
        elif self.white_player_type == "model" and self.black_player_type == "model":
            return "model(white)" if white_won else "model(black)"
        
        elif 'model' in (self.white_player_type, self.black_player_type):
            return "model" if (
                (white_won and self.white_player_type == "model") or 
                (not white_won and self.black_player_type == "model")
            ) else "player"
        
        return "player(white)" if white_won else "player(black)"
    
    def cleanup(self):
        #Inchidem Stockfish
        if hasattr(self, 'stockfish'):
            self.stockfish.close()

    