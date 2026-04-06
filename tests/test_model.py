import sys
import os
# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import chess
from dany_chess.model import AlphaZeroNet
from dany_chess.engine import best_move

def test_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AlphaZeroNet().to(device)
    model_path = "dany_chess/dany_chess_trained.pth"
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print("✅ Model loaded")
    else:
        print(f"❌ Model not found at {model_path}")
        return

    # Тест 1: позиция, где белые должны защититься от шаха ферзем на h5
    fen = "rnbqkbnr/pppp1ppp/8/4p2Q/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 2"
    board = chess.Board(fen)
    print("\n🔍 Test 1: Defend against queen threat")
    print(f"FEN: {fen}")
    print(f"Game over: {board.is_game_over()}, legal moves: {board.legal_moves.count()}")
    move = best_move(fen)
    print(f"Best move: {move}")
    if move and move.uci() in ["g7g6", "f7f6", "g8f6"]:
        print("✅ Model found a good defensive move.")
    else:
        print("❌ Model failed to find defense.")

if __name__ == "__main__":
    test_model()
