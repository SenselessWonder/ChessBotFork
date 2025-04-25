import chess
import concurrent.futures
import numpy as np
import concurrent.futures
from evaluate_board import evaluate_board
import time
import random
from threading import Lock

PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

class ChessEnv:

    def __init__(self, player_color, depth, search_time):
        self.search_time = search_time
        self.transposition_table = {}
        self.board = chess.Board()
        self.player_color = player_color
        self.ai_color = not player_color
        self.tt_lock = Lock()
        # Erstelle einen neuen Executor für jede Instanz
        self.executor = None

    global_executor = None

    def reset(self):
        """Setzt das Spiel zurück und gibt den Startzustand zurück."""
        self.board.reset()
        return self.get_state()

    def get_state(self):
        """Gibt den aktuellen Zustand des Bretts als Array zurück."""
        state = np.zeros(64)
        for square, piece in self.board.piece_map().items():
            state[square] = piece.piece_type if piece.color == chess.WHITE else -piece.piece_type
        return state

    def step(self, move):
        """Führt einen Zug aus und gibt neuen Zustand, Belohnung und Spielende zurück."""
        move_obj = chess.Move.from_uci(move)
        if move_obj in self.board.legal_moves:
            self.board.push(move_obj)
            reward = self.get_reward()
            done = self.board.is_game_over()
            return self.get_state(), reward, done
        else:
            return None, -10, True  # Ungültiger Zug gibt hohe Strafe

    def get_reward(self):
        """Belohnung basierend auf Materialvorteil."""
        material_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                           chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
        reward = sum(material_values[piece.piece_type] * (1 if piece.color == chess.WHITE else -1)
                     for piece in self.board.piece_map().values())
        return reward

    def render(self):
        """Zeigt das Brett im Terminal an."""
        print(self.board)

    def get_board_matrix(self):
        """Gibt das Brett OHNE Spiegelung zurück (nur für Weiß korrekt)."""
        board_matrix = [[None] * 8 for _ in range(8)]
        for square, piece in self.board.piece_map().items():
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            board_matrix[rank][file] = piece.symbol()  # Keine Spiegelung!
        return board_matrix

    def get_ai_move(self):
        start_time = time.time()
        best_move = None
        best_score = -float('inf')
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return None

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(legal_moves))) as executor:
                chunk_size = max(1, len(legal_moves) // 8)
                future_chunks = []
            
                for i in range(0, len(legal_moves), chunk_size):
                    chunk = legal_moves[i:i + chunk_size]
                    futures = {
                        executor.submit(
                            self.evaluate_move,
                            move,
                            start_time,
                            timeout=self.search_time/len(legal_moves)
                        ): move for move in chunk
                    }
                    future_chunks.append(futures)

                for futures in future_chunks:
                    for future in concurrent.futures.as_completed(futures, timeout=self.search_time):
                        try:
                            move = futures[future]
                            score = future.result(timeout=0.1)  # Zusätzliches Timeout pro Zug
                        
                            if score > best_score:
                                best_score = score
                                best_move = move
                            elif score == best_score and random.random() < 0.5:  # Verbesserte Randomisierung
                                best_move = move
                        except Exception as e:
                            print(f"Fehler bei Zugauswertung: {e}")

        except concurrent.futures.TimeoutError:
            print(f"Zeitüberschreitung nach {time.time() - start_time:.1f}s")
        
        return best_move or random.choice(legal_moves)

    def evaluate_move(self, move: chess.Move, start_time: float) -> float:
        board_copy = self.board.copy()
        board_copy.push(move)

        try:
            return minimax(
                board=board_copy,
                depth=5,
                alpha=-float('inf'),
                beta=float('inf'),
                transposition_table=self.transposition_table,
                start_time=start_time,
                time_limit=self.search_time - (time.time() - start_time),
                thread_pool=self.executor  # Verwende den globalen Executor
            )
        except TimeoutError:
            return -float('inf')


    def get_move_value(board, move):
        score = 0

        # Priorisiere Schlagzüge nach Materialwert
        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            score += 1.5 + (captured.piece_type if captured else 0)

        # Priorisiere Checks
        if board.gives_check(move):
            score += 2.5

        # Bestrafe das Zurückziehen in die erste Reihe
        if move.from_square in chess.SquareSet(chess.BB_RANK_1 | chess.BB_RANK_8):
            score -= 2.0

        # Bonus für Zentrumskontrolle
        if chess.square_file(move.to_square) in [3, 4] and chess.square_rank(move.to_square) in [3, 4]:
            score += 2.0

        return score


        MATERIAL_VALUES = np.array([0, 1, 3, 3, 5, 9, 1000])  # [None, P, N, B, R, Q, K]

def minimax(
        board: chess.Board,
        depth: int,
        alpha: float = -float('inf'),
        beta: float = float('inf'),
        transposition_table: dict = None,
        start_time: float = None,
        time_limit: float = None,
        thread_pool: concurrent.futures.ThreadPoolExecutor = None
) -> float:
    """Multithreaded Minimax mit Alpha-Beta Pruning und dynamischem Move Ordering."""
    # Transposition Table Lookup mit Spielerfarbe
    fen_key = f"{board.fen()}{board.turn}"


    if transposition_table and fen_key in transposition_table:
        entry = transposition_table[fen_key]
        if entry['depth'] >= depth:
            return entry['score']

    # Blattknoten oder Zeitüberschreitung
    if depth == 0 or board.is_game_over() or (time.time() - start_time > time_limit):
        return quiescence(board, alpha, beta)

    # Move Ordering mit Farbinversion
    def get_move_priority(move):
        base_score = move_ordering(board, move)
        return base_score if board.turn == chess.WHITE else -base_score

    moves = sorted(
        board.legal_moves,
        key=get_move_priority,
        reverse=board.turn == chess.WHITE
    )

    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')
    futures = []
    with (thread_pool if thread_pool else ChessEnv.global_executor) as active_executor:
        for move in moves:
            if depth > 2:  # Parallelisiere nur in oberen Ebenen
                future = active_executor.submit(
                    process_move,
                    board.copy(),
                    move,
                    depth,
                    alpha,
                    beta,
                    transposition_table,
                    start_time,
                    time_limit,
                )
                futures.append((move, future))
            else:
                score = process_move_sync(board, move, depth, alpha, beta, transposition_table, start_time,
                                          time_limit)
                best_score, alpha, beta = update_scores(score, best_score, alpha, beta, board.turn)

        # Verarbeite Futures
        for move, future in futures:
            try:
                score = future.result(timeout=time_limit - (time.time() - start_time))
                best_score, alpha, beta = update_scores(score, best_score, alpha, beta, board.turn)
            except concurrent.futures.TimeoutError:
                break

    transposition_table[fen_key] = {'depth': depth, 'score': best_score}
    return best_score


def process_move(board, move, depth, alpha, beta, tt, start_time, time_limit):
    board.push(move)
    score = minimax(
        board,
        depth - 1,
        alpha,
        beta,
        tt,
        start_time,
        time_limit,
        thread_pool=None
    )
    board.pop()
    return -score


def process_move_sync(board, move, depth, alpha, beta, tt, start_time, time_limit):
    board.push(move)
    score = minimax(board, depth - 1, alpha, beta, tt, start_time, time_limit)
    board.pop()
    return score if board.turn == chess.WHITE else -score


def update_scores(score, best_score, alpha, beta, turn):
    if turn == chess.WHITE:
        best_score = max(best_score, score)
        alpha = max(alpha, best_score)
    else:
        best_score = min(best_score, score)
        beta = min(beta, best_score)
    return best_score, alpha, beta


def move_ordering(board: chess.Board, move: chess.Move) -> int:
    """Priorisiert Schlagzüge, Checks und gute Positionen."""
    score = 0

    if board.is_castling(move):
        score += 30

    if board.is_stalemate():
        score -= 100

    # Schlagzüge priorisieren
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        score += 10 + (captured_piece.piece_type if captured_piece else 0)

    # Checks priorisieren
    if board.gives_check(move):
        score += 50

    if board.is_checkmate():
        score += 1000

    to_rank = chess.square_rank(move.to_square)
    if board.turn == chess.BLACK:
        to_rank = 7 - to_rank  # Invertiere Rang für Schwarz
    if 3 <= to_rank <= 4 and 3 <= chess.square_file(move.to_square) <= 4:
        score += 20

    return score


def quiescence(board: chess.Board, alpha: float, beta: float) -> float:
    """Quiescence Search zur Vermeidung von Horizonteffekten."""
    stand_pat = evaluate_board(board)

    if stand_pat >= beta:
        return beta
    alpha = max(alpha, stand_pat)

    for move in board.generate_legal_captures():
        board.push(move)
        score = -quiescence(board, -beta, -alpha)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha