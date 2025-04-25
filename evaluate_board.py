from dataclasses import dataclass
import chess
from typing import Dict, Optional

@dataclass
class PositionalConstants:
    CENTRAL_PAWN_BONUS: float = 0.3
    CENTRAL_KNIGHT_BONUS: float = 0.5
    DOUBLED_PAWN_PENALTY: float = 0.5
    KING_SAFETY_PENALTY: float = 0.3
    CHECKMATE_BONUS: float = 1000.0
    FIELD_CONTROL_BONUS: float = 0.1
    MINOR_PIECE_DEVELOPMENT_BONUS: float = 0.1
    MAJOR_PIECE_ACTIVITY_BONUS: float = 0.2
    PAWN_STRUCTURE_BONUS: float = 0.1

class ChessEvaluator:
    def __init__(self):
        # Erhöhte Materialwerte
        self.piece_values: Dict[str, float] = {
            'P': 2,    # Bauer
            'N': 6,    # Springer
            'B': 6.4,  # Läufer
            'R': 10,   # Turm
            'Q': 18,   # Dame
            'K': 0,    # König
            'p': -2,
            'n': -6,
            'b': -6.4,
            'r': -10,
            'q': -18,
            'k': 0
        }
        self.constants = PositionalConstants()

    def evaluate_material_change(self, board: chess.Board, move: chess.Move) -> float:
        """Bewertet Materialänderungen mit zusätzlicher Bestrafung für Verluste."""
        if not board.is_capture(move):
            return 0.0

        moving_piece = board.piece_at(move.from_square)
        captured_piece = board.piece_at(move.to_square)
        
        if not moving_piece or not captured_piece:
            return 0.0

        moving_value = abs(self.piece_values[moving_piece.symbol()])
        captured_value = abs(self.piece_values[captured_piece.symbol()])

        # Wenn der Wert der geschlagenen Figur kleiner ist
        if captured_value < moving_value:
            # Zusätzliche Bestrafung für schlechte Tausche
            return -((moving_value - captured_value) * 1.5)
        
        return captured_value - moving_value

    def evaluate_piece_position(self, piece: chess.Piece, square: int) -> float:
        """Bewertet die Position einer Figur auf dem Brett."""
        if piece.piece_type == chess.PAWN:
            if chess.square_rank(square) in [3, 4]:
                return self.constants.CENTRAL_PAWN_BONUS
            return 0.0

        if piece.piece_type == chess.KNIGHT:
            if chess.square_rank(square) in [3, 4]:
                return self.constants.CENTRAL_KNIGHT_BONUS
            return 0.0

        # Weitere Bewertungen für andere Figuren können hier hinzugefügt werden
        return 0.0

    def evaluate_board(self, board: chess.Board) -> float:
        """Bewertet das Schachbrett und gibt eine Bewertung zurück."""
        if board.is_checkmate():
            return self.constants.CHECKMATE_BONUS

        if board.is_stalemate():
            return 0.0

        score = 0.0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                score += self.piece_values[piece.symbol()]
                score += self.evaluate_piece_position(piece, square)

        return score