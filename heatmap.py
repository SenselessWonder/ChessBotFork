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


# [file name]: heatmap.py
def get_heatmap_bonus(fen: str, is_ai_white: bool) -> float:
    board = chess.Board(fen)
    bonus = 0.0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        color = "Weiß" if piece.color == chess.WHITE else "Schwarz"
        symbol = piece.symbol().upper()

        if piece.color == (chess.WHITE if is_ai_white else chess.BLACK):
            pos = square
            heatmap_value = piece_heatmaps.get(symbol, 0.0)[pos]
            print(f"+ {color} {symbol} auf {chess.square_name(pos)}: {heatmap_value:.2f}")
            bonus += heatmap_value
        else:
            file = 7 - chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            pos = chess.square(file, rank)
            heatmap_value = piece_heatmaps.get(symbol, 0.0)[pos]
            print(
                f"- {color} {symbol} auf {chess.square_name(square)} (→ {chess.square_name(pos)}): {heatmap_value:.2f}")
            bonus -= heatmap_value

    return bonus
