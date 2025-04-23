import chess
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
import concurrent.futures
import numpy as np
from evaluate_board import evaluate_board
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

    def get_ai_move(self):
        self.transposition_table.clear()
        start_time = time.time()
        timeout_left = self.search_time - (time.time() - start_time)
        if timeout_left <= 0:
            return None
        best_move = None
        best_eval = -np.inf if self.ai_color == chess.WHITE else np.inf
        depth = 1

        maximizing = (self.ai_color == chess.WHITE)
        best_eval = -float('inf') if maximizing else float('inf')

        while time.time() - start_time < self.search_time:
            current_depth = depth
            legal_moves = list(self.board.legal_moves)
            futures = []

            for move in legal_moves:
                # 👇 Erstelle eine Kopie des Bretts für jeden Zug
                board_copy = self.board.copy()
                board_copy.push(move)
                futures.append(
                    self.executor.submit(
                        self.evaluate_move_parallel,
                        board_copy,  # Korrekte Übergabe der Kopie
                        current_depth - 1,
                        -np.inf,
                        np.inf,
                        not maximizing,  # 👈 Gegnerische Perspektive
                        start_time,
                    )
                )


            # Sammle Ergebnisse mit Timeout
            try:
                for future in concurrent.futures.as_completed(futures, timeout=self.search_time - (time.time() - start_time)):
                    eval_score = future.result()
                    if (self.ai_color == chess.WHITE and eval_score > best_eval) or \
                       (self.ai_color == chess.BLACK and eval_score < best_eval):
                        best_eval = eval_score
                        best_move = legal_moves[futures.index(future)]  # 👈 Zug aus Future-Index
            except concurrent.futures.TimeoutError:
                break  # Zeit abgelaufen, breche ab
            print(f"Top-Zug auf Tiefe {current_depth}: {best_move.uci()} (Bewertung: {best_eval})")
            depth += 1

        print(f"KI suchte bis Stufe {depth-1} in {time.time()-start_time:.1f}s")
        return best_move or random.choice(list(self.board.legal_moves))  # Fallback

    def evaluate_move_parallel(self, board, depth, alpha, beta, maximizing_player, start_time):
        print(f"Starte Bewertung für Tiefe {depth}")
        return minimax(
            board,
            depth,
            alpha,
            beta,
            maximizing_player,
            self.transposition_table,
            start_time,
            self.search_time,
        )


def get_move_value(board, move):
    score = 0
    # Priorisiere Schlagzüge nach Materialwert
    if board.is_capture(move):
        captured_piece = board.piece_at(move.to_square)
        score += 10 + PIECE_VALUES[captured_piece.symbol().upper()] if captured_piece else 5

    # Priorisiere Checks
    if board.gives_check(move):
        score += 20

    # Bestrafe das Bewegen in gefährliche Felder
    attackers = len(board.attackers(not board.turn, move.to_square))
    score -= attackers * 5

    return score


MATERIAL_VALUES = np.array([0, 1, 3, 3, 5, 9, 1000])  # [None, P, N, B, R, Q, K]


def minimax(
    board,
    depth,
    alpha,
    beta,
    maximizing_player,
    transposition_table,
    start_time,
    time_limit
):
    # Überprüfe, ob die Zeit abgelaufen ist
    if time.time() - start_time > time_limit:
        raise TimeoutError()

    fen = board.fen() + (" W" if maximizing_player else " B")

    # Überprüfe die Transpositionstabelle
    if fen in transposition_table:
        entry = transposition_table[fen]
        if entry["depth"] >= depth and abs(entry["score"]) < 1000:
            return entry["score"]

    # Abbruchbedingung: Tiefe 0 oder Spielende
    if depth == 0 or board.is_game_over():
        if depth == 0:
            # Quiescence-Suche für stabile Bewertung
            score = quiescence(board, alpha, beta)
        else:
            score = evaluate_board(board, self.ai_color == chess.WHITE)
        transposition_table[fen] = {'depth': depth, 'score': score}
        return score

    # Move Ordering: Sortiere Züge nach Priorität
    sorted_moves = sorted(
        board.legal_moves,
        key=lambda m: (
            -get_move_value(board, m),  # Schlagzüge priorisieren
            board.gives_check(m),  # Checks priorisieren
            -len(board.attackers(not board.turn, m.to_square))  # Weniger Verteidigung bevorzugt
        ),
        reverse=maximizing_player  # Maximierer sortieren absteigend, Minimierer aufsteigend
    )

    best_score = -float('inf') if maximizing_player else float('inf')

    for move in sorted_moves:
        # Vermeide Brettkopien: Nutze push/pop für Effizienz
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
        except TimeoutError:
            board.pop()
            raise
        board.pop()

        # Alpha-Beta-Pruning
        if maximizing_player:
            best_score = max(best_score, current_score)
            alpha = max(alpha, best_score)
        else:
            best_score = min(best_score, current_score)
            beta = min(beta, best_score)

        if beta <= alpha:
            break  # Prune den Rest der Züge

    # Aktualisiere die Transpositionstabelle
    transposition_table[fen] = {'depth': depth, 'score': best_score}
    return best_score


def quiescence(board, alpha, beta):
    stand_pat = evaluate_board(board,board.turn == chess.WHITE)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    for move in board.generate_legal_captures():
        board.push(move)
        score = -quiescence(board, -beta, -alpha)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


class RLChessEnv(ChessEnv):
    def __init__(self, player_color):
        super().__init__(player_color, depth=3)  # Standardtiefe setzen
        self.env = make_vec_env(lambda: self, n_envs=1)  # VecEnv für schnelleres Training
        self.model = PPO("MlpPolicy", self.env, verbose=1)

    def train(self, timesteps=100000):
        """Lässt die KI für eine gewisse Zeit gegen sich selbst spielen."""
        self.model.learn(total_timesteps=timesteps)

    def get_ai_move(self):
        """Gibt einen RL-gelernten Zug zurück."""
        obs = self.get_state().reshape(1, -1)  # RL erwartet 2D-Array
        action, _states = self.model.predict(obs)
        legal_moves = list(self.board.legal_moves)
        return legal_moves[action % len(legal_moves)]  # Wählt erlaubten Zug




