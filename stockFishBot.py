import chess.engine
from board import ChessBoard

class StockfishBot:
    def __init__(self, level: int = 0):
        
        self.engine = chess.engine.SimpleEngine.popen_uci("C:/Disertatie/Stockfish/stockfish-windows-x86-64-avx2.exe")
        
        
        self.level = max(0, min(20, level))
        self.engine.configure({"Skill Level": self.level})
        self.default_move_time = 0.1
        self.default_eval_time = 0.05 if self.level < 10 else 0.1

    def get_best_move(self, board: ChessBoard):
        #Cea mai buna mutare
        result = self.engine.play(board.board, chess.engine.Limit(time=self.default_move_time))
        return result.move

    def get_evaluation(self, board: ChessBoard):
        #Evaluare
        info = self.engine.analyse(board.board, chess.engine.Limit(time=self.default_eval_time))
        evaluation = info.get("score")
        return evaluation.relative.score() if evaluation.relative else None

    def close(self):
        #inchidem Stockfish
        self.engine.quit()



