import os
import pytest
import torch
import chess
from dany_chess.engine import best_move
from tests.utils import load_tactical_positions, find_model_file

# Проверяем наличие обученной модели
model_path = find_model_file("models/dany_chess_trained.pth")
if model_path is None:
    pytest.skip("Обученная модель не найдена", allow_module_level=True)

# Загружаем позиции
TACTICAL_POSITIONS = load_tactical_positions()

@pytest.mark.parametrize("fen", TACTICAL_POSITIONS)
def test_tactical_position(fen):
    """Проверяем, что движок находит ход в каждой позиции (не пасует)."""
    move = best_move(fen)
    assert move is not None, f"Не найден ход в позиции {fen}"

# Словарь ожидаемых ходов (можно дополнить)
EXPECTED_MOVES = {
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "g8f6",
}

@pytest.mark.xfail(reason="Модель пока не всегда находит правильный тактический ход")
@pytest.mark.parametrize("fen,expected", EXPECTED_MOVES.items())
def test_tactical_expected(fen, expected):
    """Проверяем, что движок находит ожидаемый ход в тактической позиции."""
    move = best_move(fen)
    assert move is not None
    assert move.uci() == expected, f"В позиции {fen} ожидался {expected}, получен {move.uci()}"