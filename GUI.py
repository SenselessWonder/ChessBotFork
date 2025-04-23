import chess
import pygame
from ChessEnv import ChessEnv
from evaluate_board import evaluate_board

clock = pygame.time.Clock()

# Farben definieren
WHITE = (238, 238, 210)
BLACK = (118, 150, 86)

# Fenstergröße
WIDTH, HEIGHT = 800, 800
SQUARE_SIZE = WIDTH // 8



def load_svg(filename, size):
    """Lädt eine SVG-Datei in pygame und skaliert sie auf die richtige Größe."""
    image = pygame.image.load(filename)  # Lädt die SVG-Datei direkt
    return pygame.transform.scale(image, (size, size))  # Skaliert das Bild auf die Feldgröße



class GUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Schach-KI")
        self.player_color = None
        self.search_time = None
        self.choose_color()
        self.choose_search_time()
        self.env = ChessEnv(self.player_color,None, self.search_time)
        self.board = self.env.board
        self.ai_moved = False  # Initialisieren, um Fehler zu vermeiden

        # Figuren laden
        self.piece_images = {
            piece: pygame.image.load(f"pieces/{'w' if piece.isupper() else 'b'}{piece.upper()}.svg")
            for piece in "PNBRQKpnbrqk"
        }

        self.selected_square = None

        # Falls der Spieler Schwarz ist, muss die KI zuerst ziehen
        if self.player_color == chess.BLACK:
            ai_move = self.env.get_ai_move()
            if ai_move:
                self.board.push(ai_move)
                self.ai_moved = True

    def draw_board(self):
        """Zeichnet das Brett mit a1 und h8 immer weiß."""
        for vis_rank in range(8):  # Visuelle Zeile (0 = oben)
            for vis_file in range(8):  # Visuelle Spalte (0 = links)
                # Berechne Originalkoordinaten (unabhängig von der Spielerfarbe)
                if self.player_color == chess.WHITE:
                    original_file = vis_file
                    original_rank = 7 - vis_rank  # Umkehr der Zeile für Weiß-Perspektive
                else:
                    original_file = 7 - vis_file  # Spalten spiegeln
                    original_rank = vis_rank  # Zeilen nicht spiegeln

                # Farbe basierend auf Originalkoordinaten
                color = WHITE if (original_file + original_rank) % 2 == 1 else BLACK

                # Zeichne Feld
                x = vis_file * SQUARE_SIZE
                y = vis_rank * SQUARE_SIZE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self):
        piece_size = int(SQUARE_SIZE * 0.6)
        offset = (SQUARE_SIZE - piece_size) // 2
        board_matrix = self.env.get_board_matrix()

        for vis_rank in range(8):  # Visuelle Zeile (0 = oben)
            for vis_file in range(8):  # Visuelle Spalte (0 = links)
                # Originalkoordinaten berechnen
                if self.player_color == chess.WHITE:
                    original_rank = 7 - vis_rank
                    original_file = vis_file
                else:
                    original_rank = vis_rank
                    original_file = 7 - vis_file

                piece_symbol = board_matrix[original_rank][original_file]
                if piece_symbol:
                    # Skaliere das Bild
                    piece_image = self.piece_images[piece_symbol]
                    scaled_piece = pygame.transform.scale(piece_image, (piece_size, piece_size))

                    # Zeichne an visueller Position
                    x = vis_file * SQUARE_SIZE + offset
                    y = vis_rank * SQUARE_SIZE + offset
                    self.screen.blit(scaled_piece, (x, y))

    def handle_click(self, pos):
        vis_file = pos[0] // SQUARE_SIZE  # Visuelle Spalte (0 = links)
        vis_rank = pos[1] // SQUARE_SIZE  # Visuelle Zeile (0 = oben)

        # Umrechnung in Originalkoordinaten
        if self.player_color == chess.WHITE:
            original_file = vis_file
            original_rank = 7 - vis_rank
        else:
            original_file = 7 - vis_file
            original_rank = vis_rank

        square = chess.square(original_file, original_rank)
        # ... (Rest des Codes)

        if self.selected_square is None:
            # Auswahl einer Figur
            if self.board.piece_at(square) and self.board.piece_at(square).color == self.player_color:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)

            # Automatische Promotion zur Dame, falls nicht ausgewählt
            if self.board.piece_at(self.selected_square).piece_type == chess.PAWN:
                if (self.player_color == chess.WHITE and chess.square_rank(square) == 7) or \
                        (self.player_color == chess.BLACK and chess.square_rank(square) == 0):
                    move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

            if move in self.board.legal_moves:
                self.board.push(move)
                self.ai_moved = False

            self.selected_square = None

    def run(self):
        running = True
        while running:
            if self.board.turn != self.player_color and not self.ai_moved:
                ai_move = self.env.get_ai_move()
                if ai_move:
                    # Bewertung aus KI-Perspektive
                    ai_score = evaluate_board(
                        self.board,
                        self.env.ai_color == chess.WHITE
                    )
                    print(f"KI-Zug: {ai_move.uci()} | Bewertung: {ai_score:.2f} "
                          f"[{'Weiß' if self.env.ai_color == chess.WHITE else 'Schwarz'}]")
                    self.board.push(ai_move)
                    self.ai_moved = True

            # Event-Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            # Zeichne alles
            self.draw_board()
            self.draw_selected_square()
            self.draw_legal_moves()
            self.draw_pieces()

            pygame.display.flip()  # WICHTIG: Zeige die Änderungen an
            clock.tick(60)  # Begrenze auf 60 FPS (vermindert CPU-Last)


        pygame.quit()

    def choose_color(self):
        """Fragt den Spieler, ob er Weiß oder Schwarz spielen will."""
        choosing = True
        font = pygame.font.Font(None, 36)
        text_white = font.render("Drücke W für Weiß", True, (255, 255, 255))
        text_black = font.render("Drücke B für Schwarz", True, (255, 255, 255))

        while choosing:
            self.screen.fill((0, 0, 0))  # Hintergrund schwarz
            self.screen.blit(text_white, (WIDTH // 3, HEIGHT // 3))
            self.screen.blit(text_black, (WIDTH // 3, HEIGHT // 2))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.player_color = chess.WHITE
                        choosing = False
                    elif event.key == pygame.K_s:
                        self.player_color = chess.BLACK
                        choosing = False

    def draw_legal_moves(self):
        """Zeichnet die legalen Züge basierend auf der Spielerfarbe."""
        if self.selected_square is not None:
            for move in self.board.legal_moves:
                if move.from_square == self.selected_square:
                    # Umrechnung in visuelle Koordinaten
                    to_file = chess.square_file(move.to_square)
                    to_rank = chess.square_rank(move.to_square)

                    # Für Schwarz: Spalten und Zeilen spiegeln
                    if self.player_color == chess.BLACK:
                        to_file = 7 - to_file
                        to_rank = 7 - to_rank

                    # Berechne die Bildschirmposition
                    x = to_file * SQUARE_SIZE
                    y = (7 - to_rank) * SQUARE_SIZE  # Weiß-Perspektive

                    highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    highlight.fill((255, 0, 0, 100))
                    self.screen.blit(highlight, (x, y))

    def draw_selected_square(self):
        """Zeichnet die Auswahl korrekt gespiegelt."""
        if self.selected_square is not None:
            # Umrechnung in visuelle Koordinaten
            file = chess.square_file(self.selected_square)
            rank = chess.square_rank(self.selected_square)

            # Für Schwarz: Spalten und Zeilen spiegeln
            if self.player_color == chess.BLACK:
                file = 7 - file
                rank = 7 - rank

            # Berechne die Bildschirmposition
            x = file * SQUARE_SIZE
            y = (7 - rank) * SQUARE_SIZE  # Weiß-Perspektive

            pygame.draw.rect(self.screen, (100, 100, 100), (x, y, SQUARE_SIZE, SQUARE_SIZE), 3)

    def handle_promotion(self, from_square, to_square):
        """Gibt einen neuen Zug mit Umwandlungs-Piece zurück."""
        promotion_pieces = {
            "q": chess.QUEEN, "r": chess.ROOK,
            "b": chess.BISHOP, "n": chess.KNIGHT
        }

        # Auswahlmenü anzeigen
        self.screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)
        text = font.render("Wähle: Q = Dame, R = Turm, B = Läufer, N = Springer", True, (255, 255, 255))
        self.screen.blit(text, (50, HEIGHT // 3))
        pygame.display.flip()

        # Auf Eingabe warten
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.unicode.lower() in promotion_pieces:
                        promotion = promotion_pieces[event.unicode.lower()]
                        return chess.Move(from_square, to_square, promotion=promotion)
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

    def choose_search_time(self):
        """Lässt den Spieler die Rechenzeit (1-10 Sekunden) wählen."""
        choosing = True
        font = pygame.font.Font(None, 36)
        text = font.render("Rechenzeit (1-10 Sekunden):", True, (255, 255, 255))

        while choosing:
            self.screen.fill((0, 0, 0))
            self.screen.blit(text, (WIDTH // 4, HEIGHT // 3))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        self.search_time = event.key - pygame.K_0
                        choosing = False
                    elif event.key == pygame.K_0:
                        self.search_time = 10
                        choosing = False
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

    # Im __init__ ersetzen:
    # self.choose_depth() → self.choose_search_time()
    # self.ai_depth → self.search_time
    def choose_depth(self):
        """Lässt den Spieler die KI-Tiefe zwischen 1 und 5 wählen."""
        choosing = True
        font = pygame.font.Font(None, 36)
        text = font.render("Wähle die KI-Tiefe (1-5):", True, (255, 255, 255))

        while choosing:
            self.screen.fill((0, 0, 0))  # Hintergrund schwarz
            self.screen.blit(text, (WIDTH // 3, HEIGHT // 3))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_5:  # Zahl zwischen 1 und 5 gedrückt
                        self.ai_depth = event.key - pygame.K_0
                        choosing = False

    def show_end_screen(self):
        """Zeigt das Endergebnis des Spiels an."""
        result_text = "Unentschieden!"
        if self.board.is_checkmate():
            result_text = "Schachmatt! Du hast gewonnen!" if self.board.turn != self.player_color else "Schachmatt! Du hast verloren!"

        font = pygame.font.Font(None, 50)
        text = font.render(result_text, True, (255, 255, 255))
        self.screen.fill((0, 0, 0))
        self.screen.blit(text, (WIDTH // 4, HEIGHT // 3))
        pygame.display.flip()

        pygame.time.delay(3000)  # Warte 3 Sekunden
        pygame.quit()
        quit()

    def draw_material_bar(self):
        material = 0
        PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
        for piece in self.board.piece_map().values():
            value = PIECE_VALUES.get(piece.symbol().upper(), 0)
            material += value if piece.color == chess.WHITE else -value

        max_material = 39  # Maximalwert
        bar_height = HEIGHT // 2
        current = (material / max_material) * bar_height
        y = HEIGHT // 2 - current if material > 0 else HEIGHT // 2

        pygame.draw.rect(self.screen, (50, 50, 50), (WIDTH - 30, 0, 30, HEIGHT))
        pygame.draw.rect(self.screen, (200, 200, 200), (WIDTH - 30, y, 30, abs(current)))