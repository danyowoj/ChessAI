import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    """
    Residual block для улучшения сходимости глубоких сетей.
    """
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        x = F.relu(x + residual)  # skip connection + ReLU
        return x

class AlphaZeroNet(nn.Module):
    """
    AlphaZero-style нейросеть с Residual блоками.
    Вход: тензор [batch, 18, 8, 8]
    Выход: policy_logits [batch, 4672], value [batch, 1]
    """
    def __init__(self, in_channels=18, num_blocks=10, filters=128):
        super().__init__()
        self.conv_input = nn.Conv2d(in_channels, filters, kernel_size=3, padding=1)
        self.bn_input = nn.BatchNorm2d(filters)

        self.blocks = nn.Sequential(*[ResidualBlock(filters) for _ in range(num_blocks)])

        # Policy head
        self.policy_conv = nn.Conv2d(filters, 2, kernel_size=1)
        self.policy_bn = nn.BatchNorm2d(2)
        self.policy_fc = nn.Linear(2 * 8 * 8, 4672)

        # Value head
        self.value_conv = nn.Conv2d(filters, 1, kernel_size=1)
        self.value_bn = nn.BatchNorm2d(1)
        self.value_fc1 = nn.Linear(8 * 8, filters)
        self.value_fc2 = nn.Linear(filters, 1)

    def forward(self, x):
        x = F.relu(self.bn_input(self.conv_input(x)))  # [batch, filters, 8, 8]
        x = self.blocks(x)                            # [batch, filters, 8, 8]

        # Policy head
        p = F.relu(self.policy_bn(self.policy_conv(x)))  # [batch, 2, 8, 8]
        p = p.view(p.size(0), -1)                       # [batch, 2*8*8]
        p = self.policy_fc(p)                           # [batch, 4672]

        # Value head
        v = F.relu(self.value_bn(self.value_conv(x)))   # [batch, 1, 8, 8]
        v = v.view(v.size(0), -1)                       # [batch, 64]
        v = F.relu(self.value_fc1(v))                   # [batch, filters]
        v = torch.tanh(self.value_fc2(v))               # [batch, 1]

        return p, v
