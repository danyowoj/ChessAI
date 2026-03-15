import chess
import torch
from dany_chess.node import Node
from dany_chess.infer import evaluate
from dany_chess.move_mask import move_to_index

class MCTS:
    """
    Реализация Monte Carlo Tree Search (AlphaZero-style).
    """

    def __init__(self, model, device, simulations=30, c_puct=1.4):
        self.model = model
        self.device = device
        self.simulations = simulations
        self.c_puct = c_puct

    def run(self, board, temperature=1.0, add_noise=True):
        """
        Запускает MCTS из текущей позиции.

        Возвращает:
            best_move
            policy_vector (torch tensor размером 4672)
        """

        root = Node()

        policy, _ = evaluate(self.model, board, self.device)
        root.expand(policy)

        # Dirichlet noise
        if add_noise:
            moves = list(root.children.keys())
            noise = torch.distributions.Dirichlet(
                torch.ones(len(moves)) * 0.3
            ).sample()

            for i, move in enumerate(moves):
                root.children[move].P = (
                        0.75 * root.children[move].P + 0.25 * noise[i]
                )

        for _ in range(self.simulations):
            node = root
            scratch = board.copy()

            while not node.is_leaf():
                move, node = node.select_child(self.c_puct)
                scratch.push(move)

            policy, value = evaluate(self.model, scratch, self.device)

            if not scratch.is_game_over():
                node.expand(policy)

            self.backpropagate(node, value, scratch.turn)

        # === Policy target ===
        policy_target = torch.zeros(4672)
        moves = list(root.children.keys())
        visits = torch.tensor([root.children[m].N for m in moves], dtype=torch.float32)

        if temperature == 0:
            best_move = moves[visits.argmax().item()]
            policy_target[move_to_index(best_move)] = 1.0
            return best_move, policy_target

        visits = visits ** (1 / temperature)
        probs = visits / visits.sum()

        for i, move in enumerate(moves):
            idx = move_to_index(move)
            policy_target[idx] = probs[i]

        chosen_move = moves[torch.multinomial(probs, 1).item()]

        return chosen_move, policy_target

    def backpropagate(self, node, value, turn):
        """
        Распространение оценки вверх по дереву.
        """
        while node is not None:
            node.update(value if turn else -value)
            node = node.parent
            value = -value
