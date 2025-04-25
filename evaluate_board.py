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
        self.piece_values: Dict[str, float] = {
            'P': 1, 'N': 3, 'B': 3.2, 'R': 5, 'Q': 9, 'K': 0,
            'p': -1, 'n': -3, 'b': -3.2, 'r': -5, 'q': -9, 'k': 0
        }
        self.constants = PositionalConstants()
        
    def evaluate_material(self, fen: str) -> float:
        return sum(self.piece_values[c] for c in fen.split(" ")[0] if c in self.piece_values)

    def evaluate_central_control(self, board: chess.Board) -> float:
        bonus = 0.0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue
            
            if self._is_central_pawn(piece, square):
                bonus += self._get_color_multiplier(piece.color) * self.constants.CENTRAL_PAWN_BONUS
            elif self._is_central_knight(piece, square):
                bonus += self._get_color_multiplier(piece.color) * self.constants.CENTRAL_KNIGHT_BONUS
        return bonus

    def evaluate_pawn_structure(self, board: chess.Board) -> float:
        bonus = 0.0
        pawn_files = {}
        for square in board.pieces(chess.PAWN, chess.WHITE):
            file = chess.square_file(square)
            pawn_files[file] = pawn_files.get(file, 0) + 1
        
        for count in pawn_files.values():
            if count > 1:
                bonus -= self.constants.DOUBLED_PAWN_PENALTY * (count - 1)
        return bonus

    def evaluate_king_safety(self, board: chess.Board) -> float:
        safety = 0.0
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king:
            safety -= len(board.attackers(chess.BLACK, white_king)) * self.constants.KING_SAFETY_PENALTY
        if black_king:
            safety += len(board.attackers(chess.WHITE, black_king)) * self.constants.KING_SAFETY_PENALTY
        return safety

    def evaluate_position(self, board: chess.Board) -> float:
        position_score = (
            self.evaluate_central_control(board) +
            self.evaluate_pawn_structure(board) +
            self.evaluate_king_safety(board)
        )
        
        if board.is_checkmate():
            position_score += (self.constants.CHECKMATE_BONUS 
                             if board.turn == chess.WHITE else -self.constants.CHECKMATE_BONUS)
            
        return position_score

    def evaluate_board(self, board: chess.Board) -> float:
        """Bewertet die Position aus Sicht des aktuellen Spielers."""
        material = self.evaluate_material(board.fen())
        positional = self.evaluate_position(board)
        return material + positional

    @staticmethod
    def _is_central_pawn(piece: chess.Piece, square: chess.Square) -> bool:
        if piece.piece_type != chess.PAWN:
            return False
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        target_rank = rank if piece.color == chess.WHITE else 7 - rank
        return 2 <= file <= 5 and 3 <= target_rank <= 4

    @staticmethod
    def _is_central_knight(piece: chess.Piece, square: chess.Square) -> bool:
        return (piece.piece_type == chess.KNIGHT and 
                square in [chess.D4, chess.D5, chess.E4, chess.E5])

    @staticmethod
    def _get_color_multiplier(color: chess.Color) -> int:
        return 1 if color == chess.WHITE else -1