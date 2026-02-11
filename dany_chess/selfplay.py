import chess
import torch

from .engine import _mcts
from .encoder import board_to_tensor


def play_selfplay_game():
    """
    Self-play.
    :return: (state_tensor, policy_target, value)
    """

    board = chess.Board()
    history = []

    while not board.is_game_over():
        state = board_to_tensor(board)
        move, policy = _mcts.run(board)
        history.append((state, policy))
        board.push(move)

    result = board.result()

    if result == "1-0":
        value = 1.0
    elif result == "0-1":
        value = -1.0
    else:
        value = 0.0

    data = []
    for state, policy in history:
        data.append((state, policy, torch.tensor([value])))

    return data
