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
    board = chess.Board(fen)
    bonus = 0.0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        # Bestimme die Position aus KI-Perspektive
        if piece.color == (chess.WHITE if is_ai_white else chess.BLACK):
            # Eigenen Figuren: Addiere Heatmap-Wert
            pos = square
            heatmap_value = piece_heatmaps.get(piece.symbol().upper(), 0.0)[pos]
            bonus += heatmap_value
        else:
            # Gegnerische Figuren: Subtrahiere gespiegelten Heatmap-Wert
            file = 7 - chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            pos = chess.square(file, rank)
            heatmap_value = piece_heatmaps.get(piece.symbol().upper(), 0.0)[pos]
            bonus -= heatmap_value  # 👈 Gegnerische Figuren reduzieren den Bonus

    return bonus
