import chess
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
        Возвращает лучший ход.
        """

        root = Node()

        # Первичная оценка корня
        policy, _ = evaluate(self.model, board, self.device)
        root.expand(policy)

        # Основной цикл MCTS
        for _ in range(self.simulations):
            node = root
            scratch_board = board.copy()

            # 1. Selection
            while not node.is_leaf():
                move, node = node.select_child(self.c_puct)
                scratch_board.push(move)

            # 2. Evaluation
            policy, value = evaluate(self.model, scratch_board, self.device)

            # 3. Expansion
            if not scratch_board.is_game_over():
                node.expand(policy)

            # 4. Backpropagation
            self.backpropagate(node, value, scratch_board.turn)

        # Выбор хода по числу посещений
        return max(root.children.items(), key=lambda item: item[1].N)[0]

    def backpropagate(self, node, value, turn):
        """
        Распространение оценки вверх по дереву.
        """
        while node is not None:
            node.update(value if turn else -value)
            node = node.parent
            value = -value
