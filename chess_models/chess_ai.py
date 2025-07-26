from collections import namedtuple
from itertools import count
import chess
import time
from board import ChessBoard

# Structuri de date pentru evaluare
CacheEntry = namedtuple('CacheEntry', 'lower upper')
BoardState = namedtuple('BoardState', 'board score white_castling black_castling ep kp')
PieceMove = namedtuple('PieceMove', 'i j prom')

class ChessAI:
    def __init__(self, depth=3):
        # Indexare tablă 10x12
        self.ROOK_W1, self.ROOK_W2 = 91, 98
        self.ROOK_B1, self.ROOK_B2 = 21, 28

        # Valori piese pentru evaluare
        self.piece_weights = {
            "P": 102, "N": 285, "B": 322, "R": 482, "Q": 932, "K": 62000
        }

        # Tabele pentru evaluare pozitii
        self.position_scores = {
            'P': (   0,   0,   0,   0,   0,   0,   0,   0,
                     82,  85,  88,  75, 105,  85,  87,  92,
                     9,  32,  23,  46,  42,  33,  46,   9,
                     -15,  18,   0,  17,  16,   2,  17, -11,
                     -24,   5,  12,  11,   8,   3,   2, -21,
                     -20,  11,   7, -9,   -8,   0,   5, -17,
                     -29,  10,  -5, -35, -34, -12,   5, -29,
                     0,   0,   0,   0,   0,   0,   0,   0),
            'N': ( -64, -51, -73, -73, -8,  -53, -56, -68,
                   -1,  -4, 102, -34,   6,  64,  -2, -12,
                   12,  69,   3,  76,  75,  29,  64,   0,
                   26,  26,  47,  39,  35,  43,  27,  19,
                   1,   7,  33,  23,  24,  37,   4,   2,
                   -16,  12,  15,  24,  20,  17,  13, -12,
                   -21, -13,   4,   2,   4,   2, -21, -18,
                   -72, -21, -24, -22, -17, -33, -20, -67),
            'B': ( -59, -78, -82, -76, -23,-107, -37, -50,
                   -11,  20,  35, -42, -39,  31,   2, -22,
                   -9,  39, -32,  41,  52, -10,  28, -14,
                   25,  17,  20,  34,  26,  25,  15,  10,
                   13,  10,  17,  23,  17,  16,   0,   7,
                   14,  25,  24,  15,   8,  25,  20,  15,
                   19,  20,  11,   6,   7,   6,  20,  16,
                   -7,   2, -15, -12, -14, -15, -10, -10),
            'R': (  35,  29,  33,   4,  37,  33,  56,  50,
                    55,  29,  56,  67,  55,  62,  34,  60,
                    19,  35,  28,  33,  45,  27,  25,  15,
                    0,   5,  16,  13,  18,  -4,  -9,  -6,
                    -28, -35, -16, -21, -13, -29, -46, -30,
                    -42, -28, -42, -25, -25, -35, -26, -46,
                    -53, -38, -31, -26, -29, -43, -44, -53,
                    -30, -24, -18,   5,  -2, -18, -31, -32),
            'Q': (   6,   1,  -8,-104,  69,  24,  88,  26,
                     14,  32,  60, -10,  20,  76,  57,  24,
                     -2,  43,  32,  60,  72,  63,  43,   2,
                     1, -16,  22,  17,  25,  20, -13,  -6,
                     -14, -15,  -2,  -5,  -1, -10, -20, -22,
                     -30,  -6, -13, -11, -16, -11, -16, -27,
                     -36, -18,   0, -19, -15, -15, -21, -38,
                     -39, -30, -31, -13, -31, -36, -34, -42),
            'K': (   4,  54,  47, -99, -99,  60,  83, -62,
                     -32,  10,  55,  56,  56,  55,  10,   3,
                     -62,  12, -57,  44, -67,  28,  37, -31,
                     -55,  50,  11,  -4, -19,  13,   0, -49,
                     -55, -43, -52, -28, -51, -47,  -8, -50,
                     -47, -42, -43, -79, -64, -32, -29, -32,
                     -4,   3, -14, -50, -57, -18,  13,   4,
                     17,  30,  -3, -14,   6,  -1,  40,  18),
        }

        # Padding pentru tabele
        for k, table in self.position_scores.items():
            pad_line = lambda row: (0,) + tuple(x + self.piece_weights[k] for x in row) + (0,)
            self.position_scores[k] = sum((pad_line(table[i * 8 : i * 8 + 8]) for i in range(8)), ())
            self.position_scores[k] = (0,) * 20 + self.position_scores[k] + (0,) * 20

        # Constante pentru evaluare
        self.CHECKMATE_LOWER = self.piece_weights['K'] - 10 * self.piece_weights['Q']
        self.CHECKMATE_UPPER = self.piece_weights['K'] + 10 * self.piece_weights['Q']

        # Vectori de mișcare
        self.UP, self.RIGHT, self.DOWN, self.LEFT = -10, 1, 10, -1
        self.move_vectors = {
            'P': (self.UP, self.UP+self.UP, self.UP+self.LEFT, self.UP+self.RIGHT),
            'N': (self.UP+self.UP+self.RIGHT, self.RIGHT+self.UP+self.RIGHT,
                  self.RIGHT+self.DOWN+self.RIGHT, self.DOWN+self.DOWN+self.RIGHT,
                  self.DOWN+self.DOWN+self.LEFT, self.LEFT+self.DOWN+self.LEFT,
                  self.LEFT+self.UP+self.LEFT, self.UP+self.UP+self.LEFT),
            'B': (self.UP+self.RIGHT, self.DOWN+self.RIGHT,
                  self.DOWN+self.LEFT, self.UP+self.LEFT),
            'R': (self.UP, self.RIGHT, self.DOWN, self.LEFT),
            'Q': (self.UP, self.RIGHT, self.DOWN, self.LEFT,
                  self.UP+self.RIGHT, self.DOWN+self.RIGHT,
                  self.DOWN+self.LEFT, self.UP+self.LEFT),
            'K': (self.UP, self.RIGHT, self.DOWN, self.LEFT,
                  self.UP+self.RIGHT, self.DOWN+self.RIGHT,
                  self.DOWN+self.LEFT, self.UP+self.LEFT)
        }

        # Cache pentru optimizare
        self.eval_cache = {}
        self.best_move_cache = {}
        self.seen_positions = set()
        self.evaluated_positions = 0

    def convert_board_format(self, board: ChessBoard) -> str:
        #Convertim tabela python chess in formatul 10x12
        pos = [' '] * 120
        for square in chess.SQUARES:
            piece = board.board.piece_at(square)
            if piece:
                rank = 7 - chess.square_rank(square)
                file = chess.square_file(square)
                idx = 20 + rank * 10 + file + 1
                char = piece.symbol().upper() if piece.color else piece.symbol().lower()
                pos[idx] = char
            else:
                rank = 7 - chess.square_rank(square)
                file = chess.square_file(square)
                idx = 20 + rank * 10 + file + 1
                pos[idx] = '.'
            
        # Adaugam marginile tabelei
        for i in range(0, 20): pos[i] = ' '
        for i in range(100, 120): pos[i] = ' '
        for i in range(20, 100, 10): pos[i] = ' '
        for i in range(29, 109, 10): pos[i] = ' '
        
        return ''.join(pos)

    def bound(self, pos, gamma, depth, root=True):
        #Cautam o mutare mai buna
        self.evaluated_positions += 1

        #Print pentru debugging
        if root:
            # Determinam culoarea pieselor
            is_white = any(c.isupper() for c in pos.board if c in 'RNBQK')
            print(f"Evaluare la depth {depth} pentru {'alb' if is_white else 'negru'}")

        # Verificam sah mat
        if pos.score <= -self.CHECKMATE_LOWER:
            return -self.CHECKMATE_UPPER

        # Verificam cache
        entry = self.eval_cache.get((pos, depth, root), CacheEntry(-self.CHECKMATE_UPPER, self.CHECKMATE_UPPER))
        if entry.lower >= gamma: return entry.lower
        if entry.upper < gamma: return entry.upper

        def moves():
            # Incercam mai intai null move
            if depth > 2 and not root and any(c in pos.board for c in 'RBNQ'):
                yield None, -self.bound(self.rotate(pos, nullmove=True), 1-gamma, depth-3, root=False)

            # QSearch pentru cautare rapida
            if depth <= 0:
                yield None, pos.score
                #Generam doar capturi si promovari de regina
                for move in sorted(self.gen_moves(pos), key=lambda m: self.value(pos, m), reverse=True):
                    if self.value(pos, move) >= 150:  
                        score = -self.bound(self.move(pos, move), 1-gamma, depth-1, root=False)
                        yield move, score
                return

            # Incercam cea mai buna mutare din cache
            killer = self.best_move_cache.get(pos)
            if killer:
                yield killer, -self.bound(self.move(pos, killer), 1-gamma, depth-1, root=False)

            # celelalte mutari posibile
            for move in sorted(self.gen_moves(pos), key=lambda m: self.value(pos, m), reverse=True):
                #limitam numarul de noduri
                if self.evaluated_positions > 1000000:  
                    break
                score = -self.bound(self.move(pos, move), 1-gamma, depth-1, root=False)
                yield move, score

        #Evaluam toate mutarile posibile
        best, best_move = -self.CHECKMATE_UPPER, None
        for move, score in moves():
            if score > best:
                best, best_move = score, move
            if best >= gamma:
                break

        #daca nu am gasit nicio mutare buna
        if depth > 0 and best == -self.CHECKMATE_UPPER:
            #Verificam sahul pentru adversar
            flipped = self.rotate(pos, nullmove=True)
            in_check = False
            for move in self.gen_moves(flipped):
                if self.value(flipped, move) >= self.CHECKMATE_LOWER:
                    in_check = True
                    break
            #Scor 0 pentru stalemate
            if not in_check:
                best = 0 
            #Putem sa dam sah mat
            else:
                best = -self.CHECKMATE_LOWER  

        # Actualizam cache-ul
        if best >= gamma:
            self.best_move_cache[pos] = best_move
            self.eval_cache[(pos, depth, root)] = CacheEntry(best, entry.upper)
        if best < gamma:
            self.eval_cache[(pos, depth, root)] = CacheEntry(entry.lower, best)

        return best

    def rotate(self, pos, nullmove=False):
        #roteste pozitia pentru a vedea perspectiva celuilalt jucator
        return BoardState(
            pos.board[::-1].swapcase(),
            -pos.score,
            pos.black_castling, pos.white_castling,
            119 - pos.ep if pos.ep and not nullmove else 0,
            119 - pos.kp if pos.kp and not nullmove else 0,
        )

    def value(self, pos, move):
        #Calculeaza valuarea unei mutari
        i, j = move.i, move.j
        p, q = pos.board[i], pos.board[j]
        
        # Determinam daca jucam cu negrele
        is_black = pos.board.find('k') > pos.board.find('K')
        
        # scorul pozitiei fata de mutarea trecuta
        score = self.position_scores[p][j] - self.position_scores[p][i]
        
        # Bonus pentru captura
        if q.islower():
            score += self.position_scores[q.upper()][119-j]
        
        # Bonus/Penalizare pentru pozitia regelui
        if abs(j - pos.kp) < 2:
            score += self.position_scores['K'][119-j]
        
        # Bonus Rocada
        if p == 'K' and abs(i-j) == 2:
            score += self.position_scores['R'][(i+j)//2]
            score -= self.position_scores['R'][self.ROOK_W1 if j < i else self.ROOK_W2]
        
        # Promovare pion
        if p == 'P' and self.ROOK_B1 <= j <= self.ROOK_B2:
            score += self.position_scores[move.prom][j] - self.position_scores['P'][j]
        
        # Inversam scorul final pentru negru
        if is_black:
            score = -score
        
        return score

    def gen_moves(self, pos):
        #Genereaza Toate Mutarile legale
        for i, p in enumerate(pos.board):
            if not p.isupper(): continue
            for d in self.move_vectors[p]:
                for j in count(i + d, d):
                    q = pos.board[j]
                    #Evita iesirea de pe tabla si piesele noastre
                    if q.isspace() or q.isupper(): break
                    
                    # Miscarea pionului
                    if p == "P":
                        if d in (self.UP, self.UP + self.UP) and q != ".": break
                        if d == self.UP + self.UP and (i < self.ROOK_W1 + self.UP or pos.board[i + self.UP] != "."): break
                        if (d in (self.UP + self.LEFT, self.UP + self.RIGHT) and q == "." and 
                            j not in (pos.ep, pos.kp, pos.kp - 1, pos.kp + 1)): break
                        # Promovare pion
                        if self.ROOK_B1 <= j <= self.ROOK_B2:
                            for prom in "NBRQ":
                                yield PieceMove(i, j, prom)
                            break
                    
                    # Mutare normala
                    yield PieceMove(i, j, "")
                    
                    # Piesele care nu se pot glisa
                    if p in "PNK" or q.islower(): break
                    
                    # Rocada
                    if i == self.ROOK_W1 and pos.board[j + self.RIGHT] == "K" and pos.white_castling[0]:
                        yield PieceMove(j + self.RIGHT, j + self.LEFT, "")
                    if i == self.ROOK_W2 and pos.board[j + self.LEFT] == "K" and pos.white_castling[1]:
                        yield PieceMove(j + self.LEFT, j + self.RIGHT, "")

    def search(self, pos):
        #Cautare MTD bi
        self.evaluated_positions = 0
        self.seen_positions = set()
        self.eval_cache.clear()
        
        # Timpul maxim permis per depth
        MAX_TIME_PER_DEPTH = 0.5  # secunde
        search_start_time = time.time()
        
        for depth in range(1, 5):  # Cautam la depth 4
            print(f"\nÎncepem analiza pentru depth {depth} (timp total: {time.time() - search_start_time:.2f}s)")
            start_positions = self.evaluated_positions
            start_time = time.time()
            
            # Pentru depth 1, facem doar o singura evaluare rapida
            if depth == 1:
                score = self.bound(pos, 0, depth, root=True)
                print(f"  Depth 1 rapid (timp: {time.time() - start_time:.2f}s):")
                print(f"    Score: {score}")
                print(f"    Poziții evaluate: {self.evaluated_positions - start_positions}")
                yield depth, 0, score, self.best_move_cache.get(pos)
                continue
            
            # Pentru depth > 1, folosim MTD-bi cu limite de timp
            lower, upper = -self.CHECKMATE_LOWER, self.CHECKMATE_LOWER
            iteration = 0
            while lower < upper - 15:  
                current_time = time.time() - start_time
                if current_time > MAX_TIME_PER_DEPTH:
                    print(f"  Oprim depth {depth} - timp excedat ({current_time:.2f}s)")
                    break
                
                iteration += 1
                gamma = (lower + upper + 1) // 2
                score = self.bound(pos, gamma, depth, root=True)
                
                print(f"  Iterația {iteration} la depth {depth} (timp: {time.time() - start_time:.2f}s):")
                print(f"    Score: {score}")
                print(f"    Poziții evaluate: {self.evaluated_positions - start_positions}")
                
                if score >= gamma:
                    lower = score
                if score < gamma:
                    upper = score
                yield depth, gamma, score, self.best_move_cache.get(pos)
            
            print(f"Terminat depth {depth} (timp total depth: {time.time() - start_time:.2f}s):")
            print(f"  Total poziții evaluate: {self.evaluated_positions - start_positions}")
            print(f"  Timp total search: {time.time() - search_start_time:.2f}s")
            print(f"  Scor final: {(lower + upper) / 2}")

    def get_best_move(self, board: ChessBoard) -> chess.Move:
        #Gasirea celei mai bune mutari in UCI
        self.evaluated_positions = 0
        self.start_time = time.time()
        
        # Determinam daca jucam cu negrele
        is_black = board.current_player == board.black_player
        
        # Convertim în formatul intern
        pos = BoardState(
            self.convert_board_format(board),
            0,
            (board.board.has_queenside_castling_rights(chess.WHITE),
             board.board.has_kingside_castling_rights(chess.WHITE)),
            (board.board.has_queenside_castling_rights(chess.BLACK),
             board.board.has_kingside_castling_rights(chess.BLACK)),
            board.board.ep_square if board.board.ep_square else 0,
            0
        )
        
        # Rotim tabla daca jucam cu negru
        if is_black:
            pos = self.rotate(pos)
        
        best_move = None
        try:
            for depth, gamma, score, move in self.search(pos):
                if move:
                    best_move = move
                    print(f"info depth {depth} score cp {score} nodes {self.evaluated_positions}")
                if depth >= 4 or time.time() - self.start_time > 3:
                    break
        except TimeoutError:
            pass
        
        # Convertim in format python-chess
        if best_move:
            from_rank = 7 - ((best_move.i - 20) // 10)
            from_file = (best_move.i - 20) % 10 - 1
            to_rank = 7 - ((best_move.j - 20) // 10)
            to_file = (best_move.j - 20) % 10 - 1
            
            # Inversam coordonatele pentru negru
            if is_black:
                from_rank = 7 - from_rank
                from_file = 7 - from_file
                to_rank = 7 - to_rank
                to_file = 7 - to_file
            
            move = chess.Move(
                chess.square(from_file, from_rank),
                chess.square(to_file, to_rank),
                promotion=chess.QUEEN if best_move.prom == 'Q' else None
            )
            
            if move in board.board.legal_moves:
                return move
            
        return list(board.board.legal_moves)[0]

    def move(self, pos, move):
        #executam o miscare
        i, j, prom = move
        p, q = pos.board[i], pos.board[j]
        
        # Functie helper pentru actualizarea tabelei
        put = lambda board, i, p: board[:i] + p + board[i + 1:]
        
        # Copiem variabilele și resetam en passant
        board = pos.board
        white_castling, black_castling, ep, kp = pos.white_castling, pos.black_castling, 0, 0
        score = pos.score + self.value(pos, move)
        
        # Executam mutarea
        board = put(board, j, board[i])
        board = put(board, i, ".")
        
        # Actualizam drepturile de rocada
        if i == self.ROOK_W1: white_castling = (False, white_castling[1])
        if i == self.ROOK_W2: white_castling = (white_castling[0], False)
        if j == self.ROOK_B1: black_castling = (black_castling[0], False)
        if j == self.ROOK_B2: black_castling = (False, black_castling[1])
        
        # Rocada
        if p == "K":
            white_castling = (False, False)
            if abs(j - i) == 2:
                kp = (i + j) // 2
                board = put(board, self.ROOK_W1 if j < i else self.ROOK_W2, ".")
                board = put(board, kp, "R")
        
        # Mutari speciale pion
        if p == "P":
            if self.ROOK_B1 <= j <= self.ROOK_B2:
                board = put(board, j, prom)
            if j - i == 2 * self.UP:
                ep = i + self.UP
            if j == pos.ep:
                board = put(board, j + self.DOWN, ".")
        # Rotim pozitia pentru urmatorul jucator
        return self.rotate(BoardState(board, score, white_castling, black_castling, ep, kp))