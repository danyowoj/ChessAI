import torch
import torch.nn.functional as F
import chess
from dany_chess.encoder import board_to_tensor
from dany_chess.move_mask import create_legal_move_mask

INF = 1e9
EPS = 1e-8

def train_step(model, optimizer, batch, device, use_fen=True):
    """
    Универсальный шаг обучения.
    Если use_fen=True -> batch содержит (fen, policy, value).
    Если use_fen=False -> batch содержит (state, policy, value).
    """
    if use_fen:
        # Режим FEN (self-play)
        fens = [x[0] for x in batch]
        target_policy = torch.stack([x[1] for x in batch]).to(device)
        target_value = torch.stack([x[2] for x in batch]).to(device)

        boards = [chess.Board(fen) for fen in fens]
        states = torch.stack([board_to_tensor(b) for b in boards]).to(device)
        masks = torch.stack([create_legal_move_mask(b, device) for b in boards]).to(device)
    else:
        # Режим state (внешний датасет)
        states = torch.stack([x[0] for x in batch]).to(device)
        target_policy = torch.stack([x[1] for x in batch]).to(device)
        target_value = torch.stack([x[2] for x in batch]).to(device)
        # Маска не нужна, так как policy уже отмаскирована
        masks = torch.ones_like(target_policy).to(device)  # фиктивная маска, все ходы разрешены

    pred_policy_logits, pred_value = model(states)

    # Применяем маску к логитам (если маска не все единицы)
    masked_logits = pred_policy_logits + (masks - 1) * INF
    pred_probs = F.softmax(masked_logits, dim=-1)
    log_probs = torch.log(pred_probs + EPS)

    policy_loss = -(target_policy * log_probs).sum(dim=-1).mean()
    value_loss = F.mse_loss(pred_value, target_value)

    loss = policy_loss + value_loss

    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()

    return loss.item()
