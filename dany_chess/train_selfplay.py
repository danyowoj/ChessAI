import torch
import torch.optim as optim
from dany_chess.model import AlphaZeroNet
from dany_chess.selfplay import play_selfplay_game
from dany_chess.replay_buffer import ReplayBuffer
from dany_chess.trainer import train_step

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("DEVICE:", device)

model = AlphaZeroNet().to(device)
optimizer = optim.Adam(model.parameters(), lr=3e-5, weight_decay=1e-4)

buffer = ReplayBuffer()

EPOCHS = 10
GAMES_PER_EPOCH = 8          # Generate 8 games per epoch
BATCH_SIZE = 32
TRAIN_STEPS_PER_EPOCH = 500
SIMULATIONS = 300             # MCTS simulations per move
BATCH_EVAL_SIZE = 16          # Number of leaves to evaluate together

for epoch in range(EPOCHS):
    print(f"\n=== EPOCH {epoch} ===")

    # Self-play (with batch evaluation)
    for _ in range(GAMES_PER_EPOCH):
        data = play_selfplay_game(
            model, device,
            simulations=SIMULATIONS,
            batch_size=BATCH_EVAL_SIZE
        )
        for sample in data:
            buffer.add(sample)

    print("Buffer size:", len(buffer))

    # Training
    if len(buffer) >= BATCH_SIZE:
        epoch_loss = 0.0
        for step in range(TRAIN_STEPS_PER_EPOCH):
            batch = buffer.sample(BATCH_SIZE)
            loss = train_step(model, optimizer, batch, device)
            epoch_loss += loss
        avg_loss = epoch_loss / TRAIN_STEPS_PER_EPOCH
        print(f"Average loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), "../models/dany_chess_trained.pth")
