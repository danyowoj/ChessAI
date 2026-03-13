import torch
import chess
from dany_chess.encoder import board_to_tensor

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

    policy_logits = policy_logits.squeeze(0)  # [4672]
    value = value.item()

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return {}, value

    # Собираем индексы и логиты для легальных ходов
    move_indices = [move.from_square * 64 + move.to_square for move in legal_moves]
    legal_logits = policy_logits[move_indices]  # берём логиты по индексам

    # Softmax только по легальным ходам
    probs = torch.softmax(legal_logits, dim=0)

    # Формируем словарь move -> вероятность
    policy = {move: prob.item() for move, prob in zip(legal_moves, probs)}

    return policy, value
