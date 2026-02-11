import torch
import torch.nn.functional as F


def train_step(model ,optimizer, batch, device):

    states = torch.stack([x[0] for x in batch]).to(device)
    target_policy = torch.stack([x[1] for x in batch]).to(device)
    target_value = torch.stack([x[2] for x in batch]).to(device)

    pred_policy, pred_value = model(states)

    policy_loss = F.cross_entropy(pred_policy, target_policy.argmax(dim=1))
    value_loss = F.mse_loss(pred_value, target_value)

    loss = policy_loss + value_loss

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return loss.item()
