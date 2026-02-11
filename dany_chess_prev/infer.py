import torch

from .encoder import board_to_tensor


@torch.no_grad()
def evaluate_position(model, board, device):
    """
    Прогоняет позицию через сеть и возвращает value
    """

    tensor = board_to_tensor(board).unsqueeze(0).to(device)
    _, value = model(tensor)

    return value.item()
