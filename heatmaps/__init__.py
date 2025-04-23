import chess


# Hier kannst du weitere Heatmaps importieren (z.B. knight, bishop, etc.)

# Lookup-Dictionary: Großbuchstaben = Weiß, Kleinbuchstaben = Schwarz (vertikal gespiegelt)
def mirror_heatmap(heatmap):
    return heatmap[::-1]

from pawn import PAWN_HEATMAP
from .knight import KNIGHT_HEATMAP
from bishop import BISHOP_HEATMAP
from .rook import ROOK_HEATMAP
from .queen import QUEEN_HEATMAP
from .king import KING_HEATMAP

HEATMAPS = {
    'P': PAWN_HEATMAP,
    'p': PAWN_HEATMAP[::-1],  # Gespiegelte Version für Schwarz
    'N': KNIGHT_HEATMAP,
    'n': KNIGHT_HEATMAP[::-1],
    'B': BISHOP_HEATMAP,
    'b': BISHOP_HEATMAP[::-1],
    'R': ROOK_HEATMAP,
    'r': ROOK_HEATMAP[::-1],
    'Q': QUEEN_HEATMAP,
    'q': QUEEN_HEATMAP[::-1],
    'K': KING_HEATMAP,
    'k': KING_HEATMAP[::-1]
}

def get_heatmap_bonus(fen: str) -> float:
    """
    Berechnet einen Bonus basierend auf Heatmap-Daten für alle Figuren,
    indem der FEN-String geparst wird.
    """
    board = chess.Board(fen)
    bonus = 0.0
    for square, piece in board.piece_map().items():
        piece_symbol = piece.symbol()
        heatmap = HEATMAPS.get(piece_symbol)
        if heatmap is not None:
            bonus += heatmap[square]
    return bonus
