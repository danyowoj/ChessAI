import torch
import torch.nn as nn
import torch.nn.functional as F


class AlphaZeroNet(nn.Module):
    """
    AlphaZero-style нейросеть с улучшенным входным представлением:
    - общий сверточный backbone
    - policy head (вероятности ходов)
    - value head (оценка позиции)
    """

    def __init__(self, in_channels=18):
        super().__init__()

        # Общий сверточный блок
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)

        # Policy head
        self.policy_conv = nn.Conv2d(64, 2, kernel_size=1)
        self.policy_fc = nn.Linear(2 * 8 * 8, 4672)  # максимум возможных UCI-ходов

        # Value head
        self.value_conv = nn.Conv2d(64, 1, kernel_size=1)
        self.value_fc1 = nn.Linear(8 * 8, 64)
        self.value_fc2 = nn.Linear(64, 1)

    def forward(self, x):
        """
        Прямое распространение.

        :param x: [batch, 18, 8, 8]
        """
        # Общий backbone
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))

        # Policy head
        p = F.relu(self.policy_conv(x))
        p = p.view(p.size(0), -1)
        p = self.policy_fc(p)

        # Value head
        v = F.relu(self.value_conv(x))
        v = v.view(v.size(0), -1)
        v = F.relu(self.value_fc1(v))
        v = torch.tanh(self.value_fc2(v))

        return p, v
