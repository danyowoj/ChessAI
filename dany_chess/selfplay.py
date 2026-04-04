import chess
import torch
from dany_chess.mcts import MCTS
from dany_chess.move_mask import move_to_index

def play_selfplay_game(model, device, simulations=200, batch_size=16):
    board = chess.Board()
    mcts = MCTS(model, device, simulations, batch_size=batch_size)

    history = []  # (fen, policy, turn)
    move_count = 0
    root = None

    while not board.is_game_over():
        temperature = 1.0 if move_count < 20 else 0.1
        add_noise = (move_count == 0)

        root, _ = mcts.search(board, root=root, add_noise=add_noise)

        fen = board.fen()
        moves = list(root.children.keys())
        visits = torch.tensor([root.children[m].N for m in moves], dtype=torch.float32)

        if temperature == 0:
            probs = torch.zeros_like(visits)
            probs[visits.argmax()] = 1.0
        else:
            visits = visits ** (1 / temperature)
            probs = visits / (visits.sum() + 1e-8)

        chosen_idx = torch.multinomial(probs, 1).item()
        chosen_move = moves[chosen_idx]

        policy = torch.zeros(4672)
        for i, move in enumerate(moves):
            policy[move_to_index(move)] = probs[i]

        history.append((fen, policy, board.turn))
        board.push(chosen_move)
        move_count += 1
        root = root.children[chosen_move]

    result = board.result()
    data = []
    for fen, policy, turn in history:
        if result == "1-0":
            value = 1.0 if turn == chess.WHITE else -1.0
        elif result == "0-1":
            value = 1.0 if turn == chess.BLACK else -1.0
        else:
            value = 0.0
        data.append((fen, policy, torch.tensor([value], dtype=torch.float32)))
    return data
