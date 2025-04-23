import berserk

API_TOKEN = "DEIN_LICHESS_API_TOKEN"

session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session)

# Offene Herausforderungen abrufen
def get_challenges():
    return client.bots.get_challenges()

# Einen Zug auf Lichess ausführen
def make_move(game_id, move):
    client.bots.make_move(game_id, move)

# Spiel starten
def play_lichess_game():
    challenges = get_challenges()
    if not challenges:
        print("Keine offenen Herausforderungen.")
        return

    game_id = challenges[0]["id"]
    board = chess.Board()

    while not board.is_game_over():
        move = env.get_ai_move()  # KI-Zug berechnen
        make_move(game_id, move.uci())  # Zug auf Lichess ausführen
        print(f"KI hat {move} gespielt")

        # Warten auf Gegnerzug
        opponent_move = client.games.stream_game_state(game_id)["state"]["moves"].split()[-1]
        board.push(chess.Move.from_uci(opponent_move))
