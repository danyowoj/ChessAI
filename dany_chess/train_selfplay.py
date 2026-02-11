import torch
import torch.optim as optim

from dany_chess.model import AlphaZeroNet
from dany_chess.selfplay import play_selfplay_game
from dany_chess.replay_buffer import ReplayBuffer
from dany_chess.trainer import train_step


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("DEVICE: ", device)

model = AlphaZeroNet().to(device)
optimizer = optim.Adam(model.parameters(), lr=1e-3)

buffer = ReplayBuffer()

EPOCHS = 10
GAMES_PER_EPOCH = 5
BATCH_SIZE = 32


for epoch in range(EPOCHS):
    print(f"\n=== EPOCH {epoch} ===")

    # Self-play
    for _ in range(GAMES_PER_EPOCH):
        data = play_selfplay_game()
        for sample in data:
            buffer.add(sample)

    print("Buffer size: ", len(buffer))

    # Training
    if len(buffer) >= BATCH_SIZE:
        for _ in range(50):
            batch = buffer.sample(BATCH_SIZE)
            loss = train_step(model, optimizer, batch, device)

        print("Loss: ", loss)

    torch.save(model.state_dict(), "dany_chess_trained.pth")
