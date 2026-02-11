import torch
import chess

from .model import AlphaZeroNet
from .infer import evaluate_position


# Инициализация модели один раз
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = AlphaZeroNet()
_model.eval()
_model.to(_device)


def best_move(fen: str) -> chess.Move:
    """
    Основная функция движка.
    Принимает FEN, возвращает лучший ход (chess.Move).

    Алгоритм:
    - перебор всех легальных ходов
    - оценка позиции после хода через value head
    - выбор хода с максимальной value
    """

    board = chess.Board(fen)

    best_score = -float("inf")
    best_move = None

    for move in board.legal_moves:
        board.push(move)

        value = evaluate_position(_model, board, _device)

        board.pop()

        # Инверсия оценки,
        # т.к. value считается с точки зрения стороны хода
        if not board.turn:
            value = -value

        if value > best_score:
            best_score = value
            best_move = move

    return best_move
