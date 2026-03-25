import chess
import torch
import math
from dany_chess.node import Node
from dany_chess.infer import evaluate
from dany_chess.move_mask import move_to_index

class MCTS:
    """
    MCTS with batch evaluation support.
    """
    def __init__(self, model, device, simulations=30, c_puct=1.4, batch_size=1):
        self.model = model
        self.device = device
        self.simulations = simulations
        self.c_puct = c_puct
        self.batch_size = batch_size

    def search(self, board, root=None, add_noise=True):
        """
        Performs MCTS with optional batch evaluation of leaves.
        Returns (root, best_move).
        """
        if root is None:
            # Create and expand new root
            root = Node()
            policy, _ = evaluate(self.model, board, self.device)
            root.expand(policy)
            if add_noise:
                moves = list(root.children.keys())
                noise = torch.distributions.Dirichlet(
                    torch.ones(len(moves)) * 0.3
                ).sample()
                for i, move in enumerate(moves):
                    root.children[move].P = (
                        0.75 * root.children[move].P + 0.25 * noise[i]
                    )

        # Store leaves for batch evaluation
        leaves = []   # each element: (node, board_copy, turn)

        for _ in range(self.simulations):
            node = root
            scratch = board.copy()
            # Selection
            while not node.is_leaf():
                move, node = node.select_child(self.c_puct)
                scratch.push(move)

            # Store leaf for later evaluation
            leaves.append((node, scratch.copy(), scratch.turn))

            # If we have enough leaves, evaluate them in batch
            if len(leaves) >= self.batch_size:
                self._evaluate_batch(leaves)
                leaves = []

        # Evaluate remaining leaves
        if leaves:
            self._evaluate_batch(leaves)

        # Choose best move by visit count
        best_move = max(root.children.items(), key=lambda item: item[1].N)[0]
        return root, best_move

    def _evaluate_batch(self, leaves):
        """
        Evaluate a batch of leaf positions together.
        leaves: list of (node, board, turn)
        """
        if not leaves:
            return

        # Prepare batch of boards
        boards = [leaf[1] for leaf in leaves]

        # Build tensor batch
        from dany_chess.encoder import board_to_tensor
        states = torch.stack([board_to_tensor(b) for b in boards]).to(self.device)

        # Single forward pass
        policy_logits, values = self.model(states)  # values shape: [batch, 1]

        # Process each leaf
        for idx, (node, board, turn) in enumerate(leaves):
            policy_logit = policy_logits[idx]    # [4672]
            value = values[idx].item()

            # Mask illegal moves (optional, but good practice)
            from dany_chess.move_mask import create_legal_move_mask
            mask = create_legal_move_mask(board, device=self.device)
            masked_logits = policy_logit + (mask - 1) * 1e9
            probs = torch.softmax(masked_logits, dim=0)

            # Build policy dict for expansion
            policy = {}
            for move in board.legal_moves:
                idx_move = move_to_index(move)
                policy[move] = probs[idx_move].item()

            # Expand node with policy
            if not board.is_game_over():
                node.expand(policy)

            # Backpropagate value
            self._backpropagate(node, value, turn)

    def _backpropagate(self, node, value, turn):
        """Propagate value up the tree."""
        while node is not None:
            node.update(value if turn else -value)
            node = node.parent
            value = -value

    def run(self, board, temperature=1.0, add_noise=True, root=None):
        """
        Legacy interface.
        """
        root, best_move = self.search(board, root=root, add_noise=add_noise)

        policy_target = torch.zeros(4672)
        moves = list(root.children.keys())
        visits = torch.tensor([root.children[m].N for m in moves], dtype=torch.float32)

        if temperature == 0:
            policy_target[move_to_index(best_move)] = 1.0
            return best_move, policy_target

        visits = visits ** (1 / temperature)
        probs = visits / (visits.sum() + 1e-8)
        for i, move in enumerate(moves):
            policy_target[move_to_index(move)] = probs[i]

        chosen_move = moves[torch.multinomial(probs, 1).item()]
        return chosen_move, policy_target
