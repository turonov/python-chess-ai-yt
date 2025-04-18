"""
# Stockfish sozlamalari
STOCKFISH_PATH = "/path/to/stockfish"  # Stockfish'ning aniq yo'lini kiriting
ELO_LEVEL = 1000  # Stockfish'ning kuch darajasi
"""
import chess
from stockfish import Stockfish
from voice_assistant.speak import speak_uz

stockfish = Stockfish(path="/usr/games/stockfish")
stockfish.set_skill_level(5)
board = chess.Board()

def evaluate_move(move_uci):
    stockfish.set_fen_position(board.fen())
    best_move = stockfish.get_best_move()
    score_before = stockfish.get_evaluation().get('value', 0)

    board.push_uci(move_uci)
    stockfish.set_fen_position(board.fen())
    score_after = stockfish.get_evaluation().get('value', 0)
    diff = score_after - score_before

    if move_uci == best_move:
        feedback = "✅ Zo‘r yurish!"
    elif diff < -100:
        feedback = "❌ Juda zaif yurish."
    elif diff < -20:
        feedback = "⚠️ Yaxshi emas."
    else:
        feedback = "✔️ O‘rtacha yurish"

    speak_uz(feedback)
    return feedback

def run():
    print("♟ AI Shaxmat Murabbiyiga xush kelibsiz!")
    while not board.is_game_over():
        print(board)
        move = input("Yurishingiz (masalan: e2e4): ")
        if move in [m.uci() for m in board.legal_moves]:
            print(evaluate_move(move))
        else:
            print("❗ Noto‘g‘ri yurish.")

if __name__ == "__main__":
    run()
