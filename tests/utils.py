import os
import random
import chess
import torch
from dany_chess.mcts import MCTS
from dany_chess.engine import best_move as engine_best_move

def find_model_file(filename):
    """
    Ищет файл модели в нескольких стандартных местах.
    Возвращает полный путь, если файл найден, иначе None.
    """
    # Список возможных путей
    search_paths = [
        os.getcwd(), # текущая рабочая директория
        os.path.dirname(os.path.dirname(__file__)), # корень проекта (на один уровень выше tests/)
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "dany_chess")
    ]
    for base in search_paths:
        full_path = os.path.join(base, filename)
        if os.path.exists(full_path):
            return full_path
    return None

def play_game(model_white, model_black, device, simulations=200, temperature=0, add_noise=False):
    """
    Сыграть партию между двумя моделями.
    Возвращает результат с точки зрения белых: "1-0", "0-1", "1/2-1/2".
    """
    board = chess.Board()
    mcts_white = MCTS(model_white, device, simulations)
    mcts_black = MCTS(model_black, device, simulations)

    while not board.is_game_over():
        if board.turn == chess.WHITE:
            move, _ = mcts_white.run(board, temperature=temperature, add_noise=add_noise)
        else:
            move, _ = mcts_black.run(board, temperature=temperature, add_noise=add_noise)
        board.push(move)

    return board.result()

def play_vs_random(model, device, games=10, simulations=200):
    """
    Сыграть серию партий модели против случайных ходов.
    Возвращает процент побед модели (ничьи считаются за 0.5).
    """
    wins = 0
    total = 0

    for game in range(games):
        board = chess.Board()
        mcts = MCTS(model, device, simulations)

        while not board.is_game_over():
            if board.turn == chess.WHITE:  # модель играет белыми
                move, _ = mcts.run(board, temperature=0, add_noise=False)
                board.push(move)
            else:
                # случайный ход чёрных
                move = random.choice(list(board.legal_moves))
                board.push(move)

        result = board.result()
        if result == "1-0":
            wins += 1
        elif result == "1/2-1/2":
            wins += 0.5
        total += 1

    return wins / total

def load_tactical_positions(filepath=None):
    """
    Загрузить тактические позиции из EPD-файла.
    Если файл не указан, возвращает встроенный небольшой набор.
    """
    if filepath and os.path.exists(filepath):
        positions = []
        with open(filepath, 'r') as f:
            for line in f:
                parts = line.strip().split(';')
                fen = parts[0].strip()
                # можно извлечь best move, если есть
                positions.append(fen)
        return positions
    else:
        # Небольшой встроенный набор (мат в 1 ход, простые тактики)
        return [
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
            "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
            "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2P2N2/PP1P1PPP/RNBQK2R w KQkq - 0 5",
            "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
        ]
