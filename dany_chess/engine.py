import torch
import chess
import os
from dany_chess.model import AlphaZeroNet
from dany_chess.mcts import MCTS

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Параметры модели должны совпадать с теми, что использовались при обучении
_model = AlphaZeroNet(in_channels=18, num_blocks=12, filters=256).to(_device)

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "dany_chess_trained.pth")

if os.path.exists(model_path):
    print(f"✅ Loading trained model from {model_path}")
    _model.load_state_dict(torch.load(model_path, map_location=_device))
    print("Model loaded successfully")
else:
    print(f"⚠️ WARNING: Model file {model_path} not found. Using random initialized model.")

_model.eval()

# Для игры можно использовать больше симуляций
_mcts = MCTS(_model, _device, simulations=1600)

def best_move(fen: str) -> chess.Move:
    board = chess.Board(fen)
    if board.is_game_over():
        return None
    move, _ = _mcts.run(board, temperature=0, add_noise=False)
    return move
