import torch
import chess
import os

from .model import AlphaZeroNet
from .mcts import MCTS


# Инициализация модели
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_model = AlphaZeroNet().to(_device)

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "dany_chess_trained.pth")

if os.path.exists(model_path):
    print("Loading trained model...")
    _model.load_state_dict(torch.load(model_path, map_location=_device))
else:
    print("No trained model found. Using random initialized model.")

_model.eval()

# Инициализация MCTS
_mcts = MCTS(_model, _device, simulations=200)


def best_move(fen: str) -> chess.Move:
    """
    Основная функция движка.
    Использует MCTS для выбора хода.
    """

    board = chess.Board(fen)

    if board.is_game_over():
        return None

    move, _ = _mcts.run(board)

    return move
