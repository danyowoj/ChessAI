import chess
import torch
import math
from dany_chess.node import Node
from dany_chess.infer import evaluate
from dany_chess.move_mask import move_to_index

class MCTS:
    """
    Реализация Monte Carlo Tree Search (AlphaZero-style) с поддержкой reuse дерева.
    """
    def __init__(self, model, device, simulations=30, c_puct=1.4):
        self.model = model
        self.device = device
        self.simulations = simulations
        self.c_puct = c_puct

    def search(self, board, root=None, add_noise=True):
        """
        Запускает симуляции MCTS из текущей позиции.
        Если root передан, использует его как корень (подразумевается, что это дерево предыдущего хода).
        Возвращает корень после симуляций и лучший ход (на основе посещений).
        """
        if root is None:
            # Новый корень – создаём и расширяем
            root = Node()
            policy, _ = evaluate(self.model, board, self.device)
            root.expand(policy)

            # Dirichlet noise только для нового корня
            if add_noise:
                moves = list(root.children.keys())
                noise = torch.distributions.Dirichlet(
                    torch.ones(len(moves)) * 0.3
                ).sample()
                for i, move in enumerate(moves):
                    root.children[move].P = (
                        0.75 * root.children[move].P + 0.25 * noise[i]
                    )
        else:
            # При reuse корня шум не добавляется, расширение уже выполнено
            pass

        # Симуляции
        for _ in range(self.simulations):
            node = root
            scratch = board.copy()
            while not node.is_leaf():
                move, node = node.select_child(self.c_puct)
                scratch.push(move)
            policy, value = evaluate(self.model, scratch, self.device)
            if not scratch.is_game_over():
                node.expand(policy)
            self._backpropagate(node, value, scratch.turn)

        # Выбор лучшего хода по числу посещений
        best_move = max(root.children.items(), key=lambda item: item[1].N)[0]
        return root, best_move

    def run(self, board, temperature=1.0, add_noise=True, root=None):
        """
        Основной метод, совместимый со старым интерфейсом.
        Выполняет поиск и возвращает лучший ход и policy-вектор.
        Если передан root, использует его для reuse.
        """
        root, best_move = self.search(board, root=root, add_noise=add_noise)

        # Формируем policy-вектор из посещений
        policy_target = torch.zeros(4672)
        moves = list(root.children.keys())
        visits = torch.tensor([root.children[m].N for m in moves], dtype=torch.float32)

        if temperature == 0:
            # детерминированный выбор – ход с макс. посещениями уже получен
            policy_target[move_to_index(best_move)] = 1.0
            return best_move, policy_target

        # Сглаживание температуры
        visits = visits ** (1 / temperature)
        probs = visits / (visits.sum() + 1e-8)

        for i, move in enumerate(moves):
            idx = move_to_index(move)
            policy_target[idx] = probs[i]

        # Стохастический выбор (для self-play)
        chosen_move = moves[torch.multinomial(probs, 1).item()]
        return chosen_move, policy_target

    def _backpropagate(self, node, value, turn):
        """Распространение оценки вверх по дереву (внутренний метод)."""
        while node is not None:
            node.update(value if turn else -value)
            node = node.parent
            value = -value
