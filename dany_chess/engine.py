import torch
import chess

from .model import AlphaZeroNet
from .mcts import MCTS


# Инициализация модели
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = AlphaZeroNet().to(_device)
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

    return _mcts.run(board)
