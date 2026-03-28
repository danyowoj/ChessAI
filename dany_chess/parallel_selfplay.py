import torch
import multiprocessing as mp
import copy
from dany_chess.model import AlphaZeroNet
from dany_chess.selfplay import play_selfplay_game

# Устанавливаем способ запуска процессов spawn (обязательно для CUDA)
mp.set_start_method('spawn', force=True)

def worker(worker_id, model_state_dict, games_per_worker, device_str, simulations, batch_size, queue):
    """
    Функция-воркер, запускаемая в отдельном процессе.
    Создаёт свою копию модели, выполняет games_per_worker игр,
    отправляет данные в общую очередь.
    """
    device = torch.device(device_str)
    model = AlphaZeroNet().to(device)
    model.load_state_dict(model_state_dict)
    model.eval()

    local_data = []
    for game_idx in range(games_per_worker):
        data = play_selfplay_game(model, device, simulations=simulations, batch_size=batch_size)
        local_data.extend(data)

    queue.put((worker_id, local_data))

def parallel_selfplay(model, device, num_games, num_workers, simulations, batch_size):
    """
    Запускает num_games игр параллельно, используя num_workers процессов.
    Возвращает список всех позиций (data) для добавления в буфер.
    """
    if num_workers < 1:
        raise ValueError("num_workers must be at least 1")

    games_per_worker = num_games // num_workers
    extra_games = num_games % num_workers

    # Воркеры используют CPU, чтобы избежать конфликтов с CUDA
    worker_device = "cpu"
    model_state_dict = copy.deepcopy(model.state_dict())
    queue = mp.Queue()

    ctx = mp.get_context("spawn")
    processes = []

    for w_id in range(num_workers):
        games = games_per_worker
        if w_id < extra_games:
            games += 1
        p = ctx.Process(target=worker,
                        args=(w_id, model_state_dict, games, worker_device, simulations, batch_size, queue))
        processes.append(p)
        p.start()

    all_data = []
    for _ in range(num_workers):
        _, data = queue.get()
        all_data.extend(data)

    for p in processes:
        p.join()

    return all_data
