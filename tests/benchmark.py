import time
import chess
from dany_chess.engine import best_move


def benchmark(iterations=50):
    """
    Измеряет среднее время выбора хода.
    """

    board = chess.Board()
    times = []

    for i in range(iterations):
        fen = board.fen()

        start = time.time()
        move = best_move(fen)
        elapsed = time.time() - start

        if move is None:
            break

        board.push(move)
        times.append(elapsed)

        print(f"Move {i+1}: {elapsed:.4f} sec")

    avg = sum(times) / len(times)

    print("\n=== BENCHMARK ===")
    print(f"Moves tested: {len(times)}")
    print(f"Average time per move: {avg:.4f} sec")


if __name__ == "__main__":
    benchmark(iterations=50)
