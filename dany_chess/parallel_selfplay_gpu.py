import torch
import chess
import time
from dany_chess.mcts import MCTS
from dany_chess.encoder import board_to_tensor
from dany_chess.move_mask import create_legal_move_mask, move_to_index

class ParallelSelfPlay:
    def __init__(self, model, device, num_games, simulations=200, batch_size=32, c_puct=1.4, verbose=True):
        self.model = model
        self.device = device
        self.num_games = num_games
        self.simulations = simulations
        self.batch_size = batch_size
        self.c_puct = c_puct
        self.verbose = verbose
        self.reset()

    def reset(self):
        self.games = []
        for i in range(self.num_games):
            game = {
                'id': i,
                'board': chess.Board(),
                'mcts': MCTS(self.model, self.device, self.simulations, self.c_puct, batch_size=1),
                'root': None,
                'move_count': 0,
                'history': []
            }
            self.games.append(game)

    def run_games(self):
        start_time = time.time()
        if self.verbose:
            print(f"\n🎮 Starting {self.num_games} parallel games...")

        # Инициализация корней
        for game in self.games:
            game['root'], _ = game['mcts'].search(game['board'], root=None, add_noise=True)
            game['move_count'] = 0

        active_indices = list(range(self.num_games))
        total_simulations = 0
        last_report = time.time()

        # Основной цикл
        while active_indices:
            # Сбор листьев для оценки
            leaves = []
            for idx in active_indices:
                game = self.games[idx]
                board = game['board']
                root = game['root']
                mcts = game['mcts']

                # Selection
                node = root
                scratch = board.copy()
                while not node.is_leaf():
                    move, node = node.select_child(mcts.c_puct)
                    scratch.push(move)
                leaves.append((idx, node, scratch.copy(), scratch.turn))

                # Если набрали достаточно листьев – оцениваем
                if len(leaves) >= self.batch_size:
                    self._evaluate_batch(leaves)
                    leaves = []

            # Оцениваем оставшиеся листья
            if leaves:
                self._evaluate_batch(leaves)

            # Теперь после всех симуляций выбираем ходы и обновляем игры
            new_active = []
            for idx in active_indices:
                game = self.games[idx]
                board = game['board']
                root = game['root']
                move_count = game['move_count']

                if board.is_game_over():
                    continue

                temperature = 1.0 if move_count < 20 else 0.1
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

                state = board_to_tensor(board)
                mask = create_legal_move_mask(board)
                game['history'].append((state, policy, mask, board.turn))

                board.push(chosen_move)
                game['move_count'] += 1
                game['root'] = root.children[chosen_move]

                if not board.is_game_over():
                    new_active.append(idx)

            total_simulations += self.simulations * len(active_indices)
            active_indices = new_active

            # Логирование прогресса
            if self.verbose and time.time() - last_report > 2.0:
                elapsed = time.time() - start_time
                games_finished = self.num_games - len(active_indices)
                print(f"\r📊 Games: {games_finished}/{self.num_games} finished | "
                      f"Active: {len(active_indices)} | "
                      f"Simulations: {total_simulations:,} | "
                      f"Elapsed: {elapsed:.1f}s", end='', flush=True)
                last_report = time.time()

        if self.verbose:
            print()  # новая строка после прогресс-бара
            print(f"✅ All games finished in {time.time() - start_time:.1f}s")

        # Преобразование историй в обучающие данные
        all_data = []
        for game in self.games:
            board = game['board']
            result = board.result()
            for state, policy, mask, turn in game['history']:
                if result == "1-0":
                    value = 1.0 if turn == chess.WHITE else -1.0
                elif result == "0-1":
                    value = 1.0 if turn == chess.BLACK else -1.0
                else:
                    value = 0.0
                all_data.append((state, policy, mask, torch.tensor([value], dtype=torch.float32)))
        return all_data

    def _evaluate_batch(self, leaves):
        if not leaves:
            return

        boards = [leaf[2] for leaf in leaves]
        states = torch.stack([board_to_tensor(b) for b in boards]).to(self.device)

        policy_logits, values = self.model(states)

        for i, (game_idx, node, board, turn) in enumerate(leaves):
            logits = policy_logits[i]
            value = values[i].item()

            mask = create_legal_move_mask(board, device=self.device)
            masked_logits = logits + (mask - 1) * 1e9
            probs = torch.softmax(masked_logits, dim=0)

            policy = {}
            for move in board.legal_moves:
                idx = move_to_index(move)
                policy[move] = probs[idx].item()

            if not board.is_game_over():
                node.expand(policy)

            self.games[game_idx]['mcts']._backpropagate(node, value, turn)


def parallel_selfplay_gpu(model, device, num_games, simulations, batch_size, verbose=True):
    runner = ParallelSelfPlay(model, device, num_games, simulations, batch_size, verbose=verbose)
    return runner.run_games()
