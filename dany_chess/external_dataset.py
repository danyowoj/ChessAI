import torch
import numpy as np
import requests
from tqdm import tqdm
import os

class ChessAlphaDataset:
    """
    Загрузчик датасета Chess-Alpha-700K с Hugging Face.
    Возвращает батчи (state, policy, value).
    """
    def __init__(self, split='train', max_samples=None, file_url=None, local_path=None):
        self.split = split
        self.max_samples = max_samples

        # Определяем путь к файлу
        if local_path and os.path.exists(local_path):
            self.file_path = local_path
        elif file_url:
            self.file_path = self._download_file(file_url)
        else:
            # URL по умолчанию
            default_url = "https://huggingface.co/datasets/satana123/Chess-Alpha-700K/blob/main/multi_plan_dynamic_dataset.npz"
            self.file_path = self._download_file(default_url)

        # Загружаем данные
        print(f"Loading data from {self.file_path}...")
        self.data = np.load(self.file_path)
        self.length = len(self.data['states'])

        if max_samples is not None:
            self.length = min(self.length, max_samples)

        print(f"Dataset loaded: {self.length} samples.")

    def _download_file(self, url):
        local_filename = url.split('/')[-1]
        # Проверяем, не скачан ли уже файл
        if os.path.exists(local_filename):
            print(f"File already exists: {local_filename}")
            return local_filename

        print(f"Downloading {url}...")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        with open(local_filename, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        return local_filename

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        # Загружаем состояние (15 каналов)
        state = torch.from_numpy(self.data['states'][idx]).float()  # [15, 8, 8]

        # Добавляем недостающие каналы до 18 (повторяем последний канал)
        missing = state[-1:].repeat(3, 1, 1)  # берём последний канал и повторяем 3 раза
        state = torch.cat([state, missing], dim=0)  # теперь [18, 8, 8]

        # Берём лучший ход из Multi-PV (первый вариант)
        move_idx = self.data['plans'][idx, 0, 0].item()
        policy = torch.zeros(4672)
        policy[move_idx] = 1.0

        # Оценка позиции (уже нормализована)
        value = torch.tensor([self.data['evals'][idx]], dtype=torch.float32)

        return state, policy, value

    def get_batch(self, indices):
        """Возвращает батч по списку индексов."""
        states = []
        policies = []
        values = []
        for idx in indices:
            s, p, v = self[idx]
            states.append(s)
            policies.append(p)
            values.append(v)
        return torch.stack(states), torch.stack(policies), torch.stack(values)
