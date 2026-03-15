import torch
import chess
from dany_chess.encoder import board_to_tensor
from dany_chess.move_mask import create_legal_move_mask, move_to_index

INF = 1e9 # олшое число для зануления нелегальных ходов

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

    mask = create_legal_move_mask(board, device=device)
    # Вычитаем INF из нелегальных логитов
    masked_logits = policy_logits + (mask - 1) * INF
    probs = torch.softmax(masked_logits, dim=0)

    # Формируем словарь только для легальных ходов (для удобства MCTS)
    legal_moves = list(board.legal_moves)
    policy = {}
    for move in legal_moves:
        idx = move_to_index(move)
        policy[move] = probs[idx].item()

    return policy, value
