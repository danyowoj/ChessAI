import random


class ReplayBuffer:

    def __init__(self, max_size=50000):
        self.max_size = max_size
        self.buffer = []

    def add(self, sample):
        if len(self.buffer) >= self.max_size:
            self.buffer.pop(0)

        self.buffer.append(sample)

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)
