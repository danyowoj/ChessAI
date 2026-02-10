import chess
import random
from dany_chess.engine import best_move


def random_move(fen):
    """
    Случайный легальный ход.
    """
    board = chess.Board(fen)
    moves = list(board.legal_moves)
    if not moves:
        return None
    return random.choice(moves)


def play_game(engine_white, engine_black, max_moves=200):
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


def run_vs_random(games=20):
    results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0}

    for i in range(games):
        if i % 2 == 0:
            result = play_game(best_move, random_move)
        else:
            result = play_game(random_move, best_move)

        results[result] += 1
        print(f"Game {i+1}: {result}")

    print("\n=== VS RANDOM RESULTS ===")
    for k, v in results.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    run_vs_random(games=20)
