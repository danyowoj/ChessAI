import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    def __init__(self, C: int):
        super().__init__()
        self.conv1 = nn.Conv2d(C, C, 3, padding=1, bias=False)
        self.bn1   = nn.BatchNorm2d(C)
        self.conv2 = nn.Conv2d(C, C, 3, padding=1, bias=False)
        self.bn2   = nn.BatchNorm2d(C)

    def forward(self, x):
        y = self.conv1(x)
        y = F.relu(self.bn1(y), inplace=True)
        y = self.conv2(y)
        y = self.bn2(y)
        return F.relu(x + y, inplace=True)

class ChessNet(nn.Module):
    """
    Вход: (B, 12, 8, 8) — 12 бит-плоскостей (белые: PNBRQK, чёрные: pnbrqk)
    Выход: (B, 2, 8, 8):
        канал 0 -> распределение по 64 клеткам 'from'
        канал 1 -> распределение по 64 клеткам 'to'
    """
    def __init__(self, channels: int = 64, depth: int = 6):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(12, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        )
        self.body = nn.Sequential(*[ResidualBlock(channels) for _ in range(depth)])
        self.head = nn.Conv2d(channels, 2, 3, padding=1, bias=True)

    def forward(self, x):
        x = self.stem(x)
        x = self.body(x)
        x = self.head(x)    # (B, 2, 8, 8)
        return x
