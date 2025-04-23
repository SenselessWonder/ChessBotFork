import numpy as np
import chess
from pawn import PAWN_HEATMAP
from bishop import BISHOP_HEATMAP

# Heatmaps für jede Figur (Weiß-Perspektive)
piece_heatmaps = {
    'P': PAWN_HEATMAP,
    'B': BISHOP_HEATMAP,
    # 'N': KNIGHT_HEATMAP,
    # 'R': ROOK_HEATMAP,
    # 'Q': QUEEN_HEATMAP,
    # 'K': KING_HEATMAP
}


def get_heatmap_bonus(fen: str, is_ai_white: bool) -> float:
    """Berechnet den Heatmap-Bonus unter Berücksichtigung der KI-Farbe."""
    board = chess.Board(fen)
    bonus = 0.0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        # Bestimme die Heatmap-Position (spiegeln für Schwarz)
        if is_ai_white == (piece.color == chess.WHITE):
            pos = square  # Originalposition für KI = Weiß
        else:
            file = 7 - chess.square_file(square)  # Horizontal spiegeln
            rank = 7 - chess.square_rank(square)  # Vertikal spiegeln
            pos = chess.square(file, rank)

        piece_type = piece.symbol().upper()
        if piece_type in piece_heatmaps:
            bonus += piece_heatmaps[piece_type][pos]

    return bonus if is_ai_white else -bonus
