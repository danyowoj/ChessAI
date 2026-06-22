"""
Тестирование модели против Stockfish для оценки рейтинга (Elo).
Результаты сохраняются в CSV-файл для отчётности.
Поддержка параллельного выполнения партий.
Для Elo ниже 1200 используется механизм случайных ошибок.
"""

import os
import sys
import time
import chess
import csv
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from stockfish import Stockfish
from dany_chess.engine import best_move

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === НАСТРОЙКИ ===
# Убедитесь, что путь указывает на исполняемый файл stockfish
STOCKFISH_PATH = "/home/danyowoj/Downloads/stockfish-ubuntu-x86-64-avx2/stockfish/stockfish-ubuntu-x86-64-avx2"
# Диапазон Elo для тестирования (можно расширить вниз)
STOCKFISH_LEVELS = [300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200,
                    1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500]
NUM_GAMES_PER_LEVEL = 10
TIME_LIMIT = 1.0                 # секунды на ход
RESULTS_FILE = "elo_results.csv"
MAX_WORKERS = 4                  # параллельных игр

def get_stockfish_move(stockfish, board, target_elo):
    """
    Возвращает ход Stockfish с учётом целевого Elo.
    Для Elo < 1200 с вероятностью p_random выбирает случайный легальный ход.
    Для Elo >= 1200 использует стандартный skill_level.
    """
    if target_elo >= 1200:
        # Стандартный режим
        skill_level = max(0, min(20, int((target_elo - 1200) / 65)))  # 1200->0, 2500->20
        stockfish.set_skill_level(skill_level)
        stockfish.set_fen_position(board.fen())
        move_uci = stockfish.get_best_move_time(TIME_LIMIT * 1000)
        if move_uci is None:
            return None
        return chess.Move.from_uci(move_uci)
    else:
        # Режим случайных ошибок
        # Вероятность случайного хода: 0 при 1200, 0.8 при 300 (линейно)
        p_random = max(0.0, min(0.8, (1200 - target_elo) / 900.0))
        if random.random() < p_random:
            # Случайный ход
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
            return random.choice(legal_moves)
        else:
            # Ход без ошибок (используем минимальный skill_level 0)
            stockfish.set_skill_level(0)
            stockfish.set_fen_position(board.fen())
            move_uci = stockfish.get_best_move_time(TIME_LIMIT * 1000)
            if move_uci is None:
                return None
            return chess.Move.from_uci(move_uci)

def play_single_game(target_elo, model_white, game_id):
    """
    Сыграть одну партию между моделью и Stockfish (с учётом target_elo).
    Возвращает (game_id, result, error_message).
    result: 1.0 (победа модели), 0.5 (ничья), 0.0 (поражение)
    """
    try:
        stockfish = Stockfish(path=STOCKFISH_PATH, parameters={"Skill Level": 0})
        board = chess.Board()
        move_count = 0

        while not board.is_game_over():
            if (board.turn == chess.WHITE and model_white) or (board.turn == chess.BLACK and not model_white):
                # Ход модели
                fen = board.fen()
                move = best_move(fen)
                if move is None:
                    break
                board.push(move)
            else:
                # Ход Stockfish
                move = get_stockfish_move(stockfish, board, target_elo)
                if move is None:
                    break
                board.push(move)
            move_count += 1

        # Определяем результат
        if board.is_checkmate():
            winner = not board.turn
            if (winner == chess.WHITE and model_white) or (winner == chess.BLACK and not model_white):
                result = 1.0
            else:
                result = 0.0
        elif board.is_stalemate() or board.is_insufficient_material() or board.is_fivefold_repetition():
            result = 0.5
        else:
            result = 0.5

        return (game_id, result, None)
    except Exception as e:
        return (game_id, 0.0, str(e))

def save_results(elo_level, winrate, wins, total, final_elo):
    """Сохраняет результаты в CSV-файл."""
    file_exists = os.path.isfile(RESULTS_FILE)
    with open(RESULTS_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "stockfish_elo", "winrate", "wins", "total", "model_passed", "final_elo"])
        writer.writerow([
            datetime.now().isoformat(),
            elo_level,
            f"{winrate:.3f}",
            wins,
            total,
            winrate >= 0.55,
            final_elo if final_elo is not None else ""
        ])

def evaluate_elo():
    """Последовательно тестирует модель против уровней Stockfish."""
    print("🚀 Starting Elo evaluation against Stockfish...")
    print(f"Stockfish path: {STOCKFISH_PATH}")
    print(f"Games per level: {NUM_GAMES_PER_LEVEL}")
    print(f"Time limit per move: {TIME_LIMIT}s")
    print(f"Parallel workers: {MAX_WORKERS}")
    print()

    final_elo = STOCKFISH_LEVELS[0]

    for sf_elo in STOCKFISH_LEVELS:
        print(f"\n🔹 Testing against Elo {sf_elo}...")
        wins = 0
        total = 0

        tasks = [(sf_elo, (g % 2 == 0), g) for g in range(NUM_GAMES_PER_LEVEL)]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_game = {
                executor.submit(play_single_game, elo, white, gid): (gid, elo, white)
                for elo, white, gid in tasks
            }

            for future in as_completed(future_to_game):
                gid, _, white = future_to_game[future]
                try:
                    _, result, error = future.result()
                    if error:
                        print(f"  Game {gid+1} (model {'white' if white else 'black'}) ❌ error: {error}")
                        result = 0.0
                    else:
                        outcome = "✅ win" if result == 1.0 else "🤝 draw" if result == 0.5 else "❌ loss"
                        print(f"  Game {gid+1} (model {'white' if white else 'black'}) {outcome}")
                    wins += result
                    total += 1
                except Exception as e:
                    print(f"  Game {gid+1} unexpected error: {e}")
                    total += 1

        winrate = wins / total
        print(f"  Winrate: {winrate:.2%} ({wins}/{total})")
        save_results(sf_elo, winrate, wins, total, final_elo)

        if winrate >= 0.55:
            final_elo = sf_elo
            print(f"✅ Model passed Elo {sf_elo}. Moving to next level...")
        else:
            print(f"❌ Model failed at Elo {sf_elo}. Stopping.")
            final_elo = sf_elo
            break
    else:
        final_elo = STOCKFISH_LEVELS[-1]
        print(f"\n🏆 Model surpassed all levels! Estimated Elo > {final_elo}")

    print(f"\n📊 Final estimated Elo: {final_elo}")
    return final_elo

if __name__ == "__main__":
    evaluate_elo()
