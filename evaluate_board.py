import chess
import numpy as np
from numba import jit
from heatmaps import get_heatmap_bonus

# Materialwerte für die Figuren
# (Diese Werte kannst du nach Bedarf anpassen)
PIECE_VALUES = {
    'P': 1, 'p': -1,
    'N': 3, 'n': -3,
    'B': 3.2, 'b': -3.2,
    'R': 5, 'r': -5,
    'Q': 9, 'q': -9,
    'K': 100, 'k': -100
}

# JIT-optimierte Materialbewertung (ohne Heatmap)
@jit(nopython=True)
def evaluate_material(fen: str) -> float:
    score = 0.0
    # Wir nehmen an, dass der FEN-String im ersten Teil (vor dem Leerzeichen) nur das Figurenlayout enthält
    layout = fen.split(" ")[0]
    for c in layout:
        # Ziffern überspringen, da sie leere Felder darstellen
        if c >= "1" and c <= "8":
            continue
        else:
            # Da Numba keine Dicts unterstützt, verwenden wir einfache if-Statements
            if c == 'P':
                score += 1.0
            elif c == 'p':
                score -= 1.0
            elif c == 'N':
                score += 3.0
            elif c == 'n':
                score -= 3.0
            elif c == 'B':
                score += 3.2
            elif c == 'b':
                score -= 3.2
            elif c == 'R':
                score += 5.0
            elif c == 'r':
                score -= 5.0
            elif c == 'Q':
                score += 9.0
            elif c == 'q':
                score -= 9.0
            # K und k werden üblicherweise nicht bewertet
    return score


def evaluate_board(fen_or_board, is_ai_white) -> float:
    board = chess.Board(fen_or_board) if isinstance(fen_or_board, str) else fen_or_board
    fen = board.fen()
    # Materialbewertung
    material_score = evaluate_material(fen)

    # Heatmap-Bonus muss die KI-Farbe berücksichtigen
    heatmap_bonus = get_heatmap_bonus(fen)

    # Strafe-Berechnung aus KI-Perspektive
    penalty = 0.0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece or piece.color == (chess.WHITE if is_ai_white else chess.BLACK):
            continue  # Überspringe KI-Figuren

        # Angreifer = KI-Farbe, Verteidiger = Gegner
        attackers = len(board.attackers(chess.WHITE if is_ai_white else chess.BLACK, square))
        defenders = len(board.attackers(chess.BLACK if is_ai_white else chess.WHITE, square))

        if attackers > defenders:
            penalty += abs(PIECE_VALUES[piece.symbol().upper()]) * 0.5

    print(f"[DEBUG] Material: {material_score:.2f}")
    print(f"[DEBUG] Heatmap-Bonus: {heatmap_bonus:.2f}")
    print(f"[DEBUG] Penalty: {penalty:.2f}")


    score = material_score + heatmap_bonus - penalty
    return score  # Nicht mehr invertieren, da Heatmap/Bonus bereits korrigiert


board = chess.Board()
score = evaluate_board(board, is_ai_white=False)
print(f"Bewertung Startposition (KI = Schwarz): {score:.2f}")