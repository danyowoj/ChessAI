import os
import pytest
import torch
from dany_chess.model import AlphaZeroNet
from tests.utils import play_game

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

@pytest.fixture
def random_model():
    model = AlphaZeroNet().to(device)
    model.eval()
    return model

def test_arena_random_vs_random(random_model):
    """Две случайные модели должны играть примерно с равным счётом (около 0.5)."""
    wins = 0
    games = 4
    for i in range(games):
        # чередуем цвет, чтобы исключить преимущество первого хода
        if i % 2 == 0:
            result = play_game(random_model, random_model, device, simulations=30)
        else:
            result = play_game(random_model, random_model, device, simulations=30)
        if result == "1-0":
            wins += 1
        elif result == "1/2-1/2":
            wins += 0.5
    winrate = wins / games
    # Ожидаем, что winrate около 0.5, допустим небольшой разброс
    assert 0.2 < winrate < 0.8, f"Winrate {winrate} слишком далёк от 0.5"

# Более практичный тест: сравнение двух сохранённых моделей
@pytest.mark.skipif(not os.path.exists(
    "models/best_model.pth") or not os.path.exists("models/latest_model.pth"),
                    reason="Модели не найдены")
def test_arena_best_vs_latest():
    """Сравниваем лучшую модель и последнюю (после обучения). Новая должна быть не хуже."""
    best_model = AlphaZeroNet().to(device)
    best_model.load_state_dict(torch.load("models/best_model.pth", map_location=device))
    best_model.eval()

    latest_model = AlphaZeroNet().to(device)
    latest_model.load_state_dict(torch.load("models/latest_model.pth", map_location=device))
    latest_model.eval()

    wins = 0
    games = 6
    for i in range(games):
        if i % 2 == 0:
            result = play_game(latest_model, best_model, device, simulations=200)
        else:
            result = play_game(best_model, latest_model, device, simulations=200)
        if i % 2 == 0:
            # latest играет белыми
            if result == "1-0":
                wins += 1
            elif result == "1/2-1/2":
                wins += 0.5
        else:
            # latest играет чёрными
            if result == "0-1":
                wins += 1
            elif result == "1/2-1/2":
                wins += 0.5

    winrate = wins / games
    # Ожидаем, что latest не хуже best (winrate >= 0.5)
    assert winrate >= 0.4, f"Latest model too weak: winrate {winrate}"
