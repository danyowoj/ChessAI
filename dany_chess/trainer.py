import torch
import torch.nn.functional as F

INF = 1e9
EPS = 1e-8

def train_step(model, optimizer, batch, device):
    """
    batch: список кортежей (state, target_policy, mask, target_value)
    """
    states = torch.stack([x[0] for x in batch]).to(device)
    target_policy = torch.stack([x[1] for x in batch]).to(device)   # [batch, 4672]
    masks = torch.stack([x[2] for x in batch]).to(device)            # [batch, 4672]
    target_value = torch.stack([x[3] for x in batch]).to(device)     # [batch, 1]

    pred_policy_logits, pred_value = model(states)  # [batch, 4672], [batch, 1]

    # Маскируем логиты: для нелегальных ходов вычитаем INF
    masked_logits = pred_policy_logits + (masks - 1) * INF

    # Вероятности после softmax (легальные ходы получают ненулевые вероятности)
    pred_probs = F.softmax(masked_logits, dim=-1)
    log_probs = torch.log(pred_probs + EPS)  # добавляем эпсилон для численной стабильности

    # Policy loss: кросс-энтропия с целевым распределением
    policy_loss = -(target_policy * log_probs).sum(dim=-1).mean()

    # Value loss: MSE
    value_loss = F.mse_loss(pred_value, target_value)

    loss = policy_loss + value_loss

    optimizer.zero_grad()
    loss.backward()

    # Gradient clipping для предотвращения взрывных градиентов
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

    optimizer.step()

    return loss.item()
