import chess
import torch

from .node import Node
from .infer import evaluate


class MCTS:
    """
    Реализация Monte Carlo Tree Search (AlphaZero-style).
    """

    def __init__(self, model, device, simulations=100, c_puct=1.4):
        self.model = model
        self.device = device
        self.simulations = simulations
        self.c_puct = c_puct

    def run(self, board):
        """
        Запускает MCTS из текущей позиции.

        Возвращает:
            best_move
            policy_vector (torch tensor размером 4672)
        """

        root = Node()

        # Первичная оценка
        policy, _ = evaluate(self.model, board, self.device)
        root.expand(policy)

        for _ in range(self.simulations):
            node = root
            scratch_board = board.copy()

            # Selection
            while not node.is_leaf():
                move, node = node.select_child(self.c_puct)
                scratch_board.push(move)

            # Evaluation
            policy, value = evaluate(self.model, scratch_board, self.device)

            # Expansion
            if not scratch_board.is_game_over():
                node.expand(policy)

            # Backpropagation
            self.backpropagate(node, value, scratch_board.turn)

        # === Формируем policy target ===
        policy_target = torch.zeros(4672)

        total_visits = sum(child.N for child in root.children.values())

        for move, child in root.children.items():
            move_index = self.move_to_index(move)
            policy_target[move_index] = child.N / total_visits

        # Лучший ход
        best_move = max(root.children.items(), key=lambda item: item[1].N)[0]

        return best_move, policy_target

    def backpropagate(self, node, value, turn):
        """
        Распространение оценки вверх по дереву.
        """
        while node is not None:
            node.update(value if turn else -value)
            node = node.parent
            value = -value

    def move_to_index(selfself, move):
        """
        Преобразование хода в индекс policy-вектора.
        """
        return move.from_square * 64 + move.to_square
