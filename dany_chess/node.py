import math


class Node:
    """
    Узел дерева MCTS

    Хранит статистику:
    - N: число посещений
    - W: суммарная ценность
    - Q: средняя ценность (W / N)
    - P: априорная вероятность хода (из policy-head)
    """

    def __init__(self, parent=None, prior=0.0):
        self.parent = parent
        self.children = {}  # move -> Node

        self.P = prior
        self.N = 0
        self.W = 0.0
        self.Q = 0.0

    def is_leaf(self):
        """Проверка: является ли узел листом"""
        return len(self.children) == 0

    def expand(self, priors):
        """
        Expansion:
        добавляет дочерние узлы на основе policy-head

        priors: dict(move -> probability)
        """
        for move, p in priors.items():
            if move not in self.children:
                self.children[move] = Node(parent=self, prior=p)

    def select_child(self, c_puct):
        """
        Selection:
        выбор дочернего узла по формуле PUCT
        """
        best_score = -float("inf")
        best_move = None
        best_child = None

        for move, child in self.children.items():
            u = c_puct * child.P * math.sqrt(self.N) / (1 + child.N)
            score = child.Q + u

            if score > best_score:
                best_score = score
                best_move = move
                best_child = child

        return best_move, best_child

    def update(self, value):
        """
        Backpropagation:
        обновляет статистику узла
        """
        self.N += 1
        self.W += value
        self.Q = self.W / self.N
