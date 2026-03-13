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

def test_random_vs_random(random_model):
    """Случайная модель против случайных ходов – около 0.5."""
    winrate = play_vs_random(random_model, device, games=10, simulations=30)
    assert 0.2 < winrate < 0.8, f"Winrate {winrate} не около 0.5"

@pytest.mark.skipif(not os.path.exists("models/dany_chess_trained.pth"), reason="Обученная модель не найдена")
def test_trained_vs_random():
    """Обученная модель должна выигрывать у случайного игрока с высоким процентом."""
    model = AlphaZeroNet().to(device)
    model.load_state_dict(torch.load("models/dany_chess_trained.pth", map_location=device))
    model.eval()

    winrate = play_vs_random(model, device, games=20, simulations=200)
    assert winrate > 0.7, f"Trained model too weak against random: {winrate}"
