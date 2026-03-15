import chess
import torch
from dany_chess.encoder import board_to_tensor
from dany_chess.mcts import MCTS
from dany_chess.move_mask import create_legal_move_mask

def play_selfplay_game(model, device, simulations=200):
    board = chess.Board()
    mcts = MCTS(model, device, simulations)

    history = []  # каждый элемент: (state, policy, mask, turn)
    move_count = 0

    while not board.is_game_over():
        temperature = 1.0 if move_count < 20 else 0.1
        move, policy = mcts.run(
            board,
            temperature=temperature,
            add_noise=True
        )
        state = board_to_tensor(board)
        mask = create_legal_move_mask(board)  # тензор [4672]
        history.append((state, policy, mask, board.turn))
        board.push(move)
        move_count += 1

    result = board.result()

    # Определяем value для каждой позиции с учётом цвета
    data = []
    for state, policy, mask, turn in history:
        if result == "1-0":
            value = 1.0 if turn == chess.WHITE else -1.0
        elif result == "0-1":
            value = 1.0 if turn == chess.BLACK else -1.0
        else:
            value = 0.0

        data.append((state, policy, mask, torch.tensor([value], dtype=torch.float32)))

    return data
