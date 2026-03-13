import torch
import torch.optim as optim

from dany_chess.model import AlphaZeroNet
from dany_chess.selfplay import play_selfplay_game
from dany_chess.replay_buffer import ReplayBuffer
from dany_chess.trainer import train_step
from dany_chess.arena import arena
from dany_chess.elo import update_elo


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

best_model = AlphaZeroNet().to(device)
new_model = AlphaZeroNet().to(device)

optimizer = optim.Adam(new_model.parameters(), lr=1e-3)

buffer = ReplayBuffer()

best_elo = 1000
new_elo = 1000

EPOCHS = 10
GAMES_PER_EPOCH = 2
BATCH_SIZE = 64


for epoch in range(EPOCHS):

    print(f"\n=== EPOCH {epoch} ===")

    # 1. Self-play
    for i in range(GAMES_PER_EPOCH):
        print(f"Self-play game {i + 1}/{GAMES_PER_EPOCH}")
        data = play_selfplay_game(best_model, device)
        for sample in data:
            buffer.add(sample)

    print("Buffer size:", len(buffer))

    # 2. Training
    if len(buffer) >= BATCH_SIZE:
        for _ in range(100):
            batch = buffer.sample(BATCH_SIZE)
            loss = train_step(new_model, optimizer, batch, device)

        print("Training loss:", loss)

    # 3. Arena comparison
    winrate = arena(new_model, best_model, device, games=6)
    print("Arena winrate:", winrate)

    # 4. Elo update
    new_elo = update_elo(new_elo, best_elo, winrate)
    print("New Elo:", new_elo)

    # 5. Replace best model if improved
    if winrate > 0.55:
        print("New model becomes BEST")
        best_model.load_state_dict(new_model.state_dict())
        best_elo = new_elo
        torch.save(best_model.state_dict(), "best_model.pth")
    else:
        print("Model rejected")

    torch.save(new_model.state_dict(), "latest_model.pth")
