import chess
from dany_chess.mcts import MCTS


def play_game(model_white, model_black, device, simulations=200):

    board = chess.Board()
    mcts_white = MCTS(model_white, device, simulations)
    mcts_black = MCTS(model_black, device, simulations)

    while not board.is_game_over():

        if board.turn:
            move, _ = mcts_white.run(board, temperature=0, add_noise=False)
        else:
            move, _ = mcts_black.run(board, temperature=0, add_noise=False)

        board.push(move)

    return board.result()


def arena(model_new, model_best, device, games=20):

    wins = 0
    draws = 0

    for i in range(games):

        if i % 2 == 0:
            result = play_game(model_new, model_best, device)
        else:
            result = play_game(model_best, model_new, device)

        if result == "1-0":
            wins += 1
        elif result == "1/2-1/2":
            draws += 1

    winrate = (wins + 0.5 * draws) / games
    return winrate
