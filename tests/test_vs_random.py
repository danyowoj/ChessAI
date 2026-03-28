import os
import pytest
import torch
import random
from dany_chess.model import AlphaZeroNet
from tests.utils import play_vs_random

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

@pytest.fixture
def random_model():
    model = AlphaZeroNet().to(device)
    model.eval()
    return model

@pytest.mark.skipif(not os.path.exists("models/dany_chess_trained.pth"), reason="Обученная модель не найдена")
def test_trained_vs_random():
    """Обученная модель должна выигрывать у случайного игрока с высоким процентом."""
    model = AlphaZeroNet().to(device)
    model.load_state_dict(torch.load("models/dany_chess_trained.pth", map_location=device))
    model.eval()

    winrate = play_vs_random(model, device, games=20, simulations=200)
    assert winrate > 0.7, f"Trained model too weak against random: {winrate}"
