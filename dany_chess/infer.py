import torch
import chess
from .encoder import board_to_tensor


@torch.no_grad()
def evaluate(model, board, device):
    """
    Прогон позиции через нейросеть.

    Возвращает:
    - policy: dict(move -> probability)
    - value: оценка позиции [-1, 1]
    """

    x = board_to_tensor(board).unsqueeze(0).to(device)
    policy_logits, value = model(x)

    policy_logits = policy_logits.squeeze(0)

    policy = {}
    legal_moves = list(board.legal_moves)

    if not legal_moves:
        return policy, value.item()

    probs = torch.softmax(policy_logits[:len(legal_moves)], dim=0)

    for move, p in zip(legal_moves, probs):
        policy[move] = p.item()

    return policy, value.item()
