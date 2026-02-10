import chess
import random
from dany_chess.engine import best_move
from dany_chess_prev.engine import best_move as best_move_prev


def play_game(engine_white, engine_black, max_moves=200):
    """
    Игра между двумя движками.

    :return: Результат партии в формате chess.Board.result().
    """

    board = chess.Board()
    moves = 0

    while not board.is_game_over() and moves < max_moves:
        if board.turn == chess.WHITE:
            move = engine_white(board.fen())
        else:
            move = engine_black(board.fen())

        if move is None:
            break

        board.push(move)
        moves += 1

    result = board.result()
    if result == "*":
        result = "1/2-1/2"

    return result


def run_selfplay(games=20):
    """
    Запускает серию партий движок vs движок
    """

    results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0}

    for i in range(games):
        # Чередуем цвета
        if i % 2 == 0:
            result = play_game(best_move, best_move_prev)
        else:
            result = play_game(best_move_prev, best_move)

        results[result] += 1
        print(f"Game {i+1}: {result}")

    print("\n=== SELF-PLAY RESULTS ===")
    for k, v in results.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    run_selfplay(games=20)
