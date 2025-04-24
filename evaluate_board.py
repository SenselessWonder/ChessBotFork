import chess
import numpy as np
from numba import jit

# Materialwerte aus Weiß-Perspektive
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3.2,
    'R': 5, 'Q': 9, 'K': 0,
    'p': -1, 'n': -3, 'b': -3.2,
    'r': -5, 'q': -9, 'k': 0
}

def calculate_material(fen: str) -> float:
    score = 0.0
    for c in fen.split(" ")[0]:
        if c in PIECE_VALUES:
            score += PIECE_VALUES[c]
    return score


def calculate_positional(board: chess.Board) -> float:
    position_bonus = 0.0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue

        # Bonus für zentrale Bauern
        if piece.piece_type == chess.PAWN:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            if 2 <= file <= 5 and 3 <= rank <= 4:
                position_bonus += 0.3 if piece.color == chess.WHITE else -0.3

        # Bonus für Springer im Zentrum
        elif piece.piece_type == chess.KNIGHT:
            if square in [chess.D4, chess.D5, chess.E4, chess.E5]:
                position_bonus += 0.5 if piece.color == chess.WHITE else -0.5

    # 3. Strafe für Doppelbauern
    pawn_files = {}
    for square in board.pieces(chess.PAWN, chess.WHITE):
        file = chess.square_file(square)
        pawn_files[file] = pawn_files.get(file, 0) + 1
    for count in pawn_files.values():
        if count > 1:
            position_bonus -= 0.5 * (count - 1)

    # 4. Königssicherheit (Beispiel: Anzahl der nahen Bauern)
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    king_safety = 0.0
    if white_king:
        king_safety += len(board.attackers(chess.BLACK, white_king)) * -0.3
    if black_king:
        king_safety += len(board.attackers(chess.WHITE, black_king)) * 0.3

    #5. Matt Belohnung
    if board.is_checkmate():
        position_bonus += 1000 if board.turn == chess.WHITE else -1000

    #6. Bonus für felder abdeckung
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == board.turn:
            for target_square in chess.SQUARES:
                if board.is_attacked_by(not board.turn, target_square):
                    if square in chess.SQUARES:
                        position_bonus += 0.1 if piece.color == chess.WHITE else -0.1

    #7. Bonus für Figurenentwicklung
    for piece in board.piece_map().values():
        if piece.color == board.turn:
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                position_bonus += 0.1 if piece.color == chess.WHITE else -0.1

    #8. Bonus für Figurenaktivität
    for piece in board.piece_map().values():
        if piece.color == board.turn:
            if piece.piece_type in [chess.ROOK, chess.QUEEN]:
                position_bonus += 0.2 if piece.color == chess.WHITE else -0.2

    #9. Bonus Bauernstruktur
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == board.turn and piece.piece_type == chess.PAWN:
            if square in [chess.A2, chess.B2, chess.C2, chess.D2, chess.E2, chess.F2, chess.G2, chess.H2]:
                position_bonus += 0.1 if piece.color == chess.WHITE else -0.1



    score = position_bonus + king_safety
    return score

def evaluate_board(board: chess.Board) -> float:
    """Bewertet die Position aus Sicht des aktuellen Spielers (board.turn)."""
    material = calculate_material(board.fen())
    positional = calculate_positional(board)

    score = material + positional

    if board.is_checkmate():
        return -1000 if board.turn == chess.WHITE else 1000
    return score