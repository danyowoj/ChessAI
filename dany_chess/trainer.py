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

    # Применяем маску к логитам
    masked_logits = pred_policy_logits + (masks - 1) * INF

    # Предсказанные вероятности после маски
    pred_probs = F.softmax(masked_logits, dim=-1)

    # KL-div: sum(target * log(target / pred))
    # Лучше использовать log_pred и target с небольшим эпсилоном для численной стабильности
    log_pred_probs = torch.log(pred_probs + EPS)
    policy_loss = F.kl_div(log_pred_probs, target_policy, reduction='batchmean')

    value_loss = F.mse_loss(pred_value, target_value)

    loss = policy_loss + value_loss

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return loss.item()
