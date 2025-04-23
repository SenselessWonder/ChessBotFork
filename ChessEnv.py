import chess
import concurrent.futures
import numpy as np
#from evaluate_board import evaluate_board
import time
import random

PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

class ChessEnv:
    def __init__(self, player_color, depth, search_time):
        self.search_time = search_time
        self.transposition_table = {}
        self.board = chess.Board()
        self.player_color = player_color
        self.ai_color = not player_color
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)


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

    opening_book = {
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR": ["e2e4", "d2d4"],
        # ... Weitere Positionen
    }

    def __init__(self, search_time=5):
        self.board = chess.Board()
        self.search_time = search_time
        self.transposition_table = {}

    def get_ai_move(self):
        base_depth = 3
        if len(self.board.move_stack) < 8:  # Erhöhte Tiefe in der Eröffnung
            base_depth = 4
        elif self.board.is_endgame():  # Reduzierte Tiefe im Endspiel
            base_depth = 5

        start_time = time.time()
        best_move = None
        best_score = -float('inf')
        legal_moves = list(self.board.legal_moves)

        try:
            # Bewerte alle legalen Züge parallel
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(
                        self.evaluate_move,
                        move,
                        start_time
                    ): move for move in legal_moves
                }

                for future in concurrent.futures.as_completed(futures, timeout=self.search_time):
                    move = futures[future]
                    score = future.result()

                    if score > best_score or (score == best_score and random.random() < 0.3):
                        best_score = score
                        best_move = move

        except (concurrent.futures.TimeoutError, TimeoutError):
            print(f"Zeitüberschreitung nach {time.time() - start_time:.1f}s")

        # Fallback: Zufälliger Zug
        return best_move or random.choice(legal_moves)

    def evaluate_move(self, move: chess.Move, start_time: float) -> float:
        """Bewertet einen einzelnen Zug"""
        board_copy = self.board.copy()
        board_copy.push(move)

        try:
            return minimax(
                board=board_copy,
                depth=3,  # Basis-Tiefe
                alpha=-float('inf'),
                beta=float('inf'),
                transposition_table=self.transposition_table,
                start_time=start_time,
                time_limit=self.search_time - (time.time() - start_time)
            )
        except TimeoutError:
            return -float('inf')  # Timeout als schlechteste Bewertung


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

import chess
import time


def minimax(
        board: chess.Board,
        depth: int,
        alpha: float = -float('inf'),
        beta: float = float('inf'),
        maximizing_player: bool = None,
        transposition_table: dict = None,
        start_time: float = None,
        time_limit: float = None
) -> float:
    """
    Universelle Minimax-Implementierung für Schach.
    Bewertet Positionen immer aus Sicht des aktuellen Spielers (board.turn).
    """

    # Initialisiere Standardwerte
    if maximizing_player is None:
        maximizing_player = board.turn == chess.WHITE

    if transposition_table is None:
        transposition_table = {}

    if start_time is None:
        start_time = time.time()

    if time_limit is None:
        time_limit = float('inf')

    # Zeitkontrolle
    if time.time() - start_time > time_limit:
        raise TimeoutError("Zeitüberschreitung")

    # Transposition Table Lookup
    fen = board.fen()
    if fen in transposition_table:
        entry = transposition_table[fen]
        if entry['depth'] >= depth:
            return entry['score']

    # Blattknoten oder Endstellung
    if depth == 0 or board.is_game_over():
        score = quiescence(board, alpha, beta) if depth == 0 else evaluate_board(board)
        transposition_table[fen] = {'depth': depth, 'score': score}
        return score

    # Zuggenerierung mit Move Ordering
    legal_moves = sorted(
        board.legal_moves,
        key=lambda m: move_ordering(board, m),
        reverse=maximizing_player
    )

    best_score = -float('inf') if maximizing_player else float('inf')

    for move in legal_moves:
        board.push(move)
        try:
            current_score = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                not maximizing_player,
                transposition_table,
                start_time,
                time_limit
            )
        finally:
            board.pop()

        # Alpha-Beta-Pruning
        if maximizing_player:
            best_score = max(best_score, current_score)
            alpha = max(alpha, best_score)
        else:
            best_score = min(best_score, current_score)
            beta = min(beta, best_score)

        if beta <= alpha:
            break

    transposition_table[fen] = {'depth': depth, 'score': best_score}
    return best_score


def move_ordering(board: chess.Board, move: chess.Move) -> int:
    """Priorisiert Schlagzüge, Checks und gute Positionen."""
    score = 0

    # Schlagzüge priorisieren
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        score += 10 + (captured_piece.piece_type if captured_piece else 0)

    # Checks priorisieren
    if board.gives_check(move):
        score += 50

    # Zentrumskontrolle
    if chess.square_file(move.to_square) in [3, 4] and chess.square_rank(move.to_square) in [3, 4]:
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


def evaluate_board(board: chess.Board) -> float:
    """Bewertet die Position aus Sicht des aktuellen Spielers (board.turn)."""
    # Einfache Materialbewertung (+0.1 pro Zentrumsbauer)
    score = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        # Materialwert
        value = get_piece_value(piece)
        score += value if piece.color == board.turn else -value

        # Positionsbonus für Bauern
        if piece.piece_type == chess.PAWN:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            if 2 <= file <= 5 and 3 <= rank <= 4:
                score += 0.1 if piece.color == board.turn else -0.1

    return score


def get_piece_value(piece: chess.Piece) -> float:
    """Standard Materialwerte"""
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3.2,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    return values[piece.piece_type]
