import chess
from player import Player

class ChessBoard:
    
    def __init__(self):
        self.board = chess.Board()
        self.board_state_history = [self.board.copy()]
        self._setup_players()
    
    def _setup_players(self):
        #Inițializează jucătorii
        self.white_player = Player("white", self.board)
        self.black_player = Player("black", self.board)
        self.current_player = self.white_player
    
    def make_move(self, move_uci, player):
        if self.is_game_over():
            return False
            
        try:
            move = chess.Move.from_uci(move_uci)
            if move not in self.board.legal_moves:
                return False
            
            # Executăm mutarea
            self.board.push(move)
            self.board_state_history.append(self.board.copy())
            
            # Schimbăm jucătorul
            self.current_player = (
                self.black_player 
                if self.current_player == self.white_player 
                else self.white_player
            )
            
            return True
        except ValueError:
            return False
    
    def is_game_over(self):
        return self.board.is_game_over()
    
    def is_checkmate(self):
        return self.board.is_checkmate()
    
    def is_stalemate(self):
        return self.board.is_stalemate()
    

