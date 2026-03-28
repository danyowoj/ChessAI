import torch
import torch.optim as optim
from dany_chess.model import AlphaZeroNet
from dany_chess.replay_buffer import ReplayBuffer
from dany_chess.trainer import train_step
from dany_chess.parallel_selfplay import parallel_selfplay

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("DEVICE:", device)

    model = AlphaZeroNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=3e-5, weight_decay=1e-4)

    buffer = ReplayBuffer(max_size=200000)

    EPOCHS = 8
    GAMES_PER_EPOCH = 8
    NUM_WORKERS = 4
    BATCH_SIZE = 32
    TRAIN_STEPS_PER_EPOCH = 1024
    SIMULATIONS = 512
    BATCH_EVAL_SIZE = 16

    for epoch in range(EPOCHS):
        print(f"\n=== EPOCH {epoch} ===")

        print("Generating self‑play games...")
        new_data = parallel_selfplay(model, device, GAMES_PER_EPOCH, NUM_WORKERS,
                                     SIMULATIONS, BATCH_EVAL_SIZE)

        for sample in new_data:
            buffer.add(sample)

        print(f"Buffer size: {len(buffer)}")

        if len(buffer) >= BATCH_SIZE:
            epoch_loss = 0.0
            for step in range(TRAIN_STEPS_PER_EPOCH):
                batch = buffer.sample(BATCH_SIZE)
                loss = train_step(model, optimizer, batch, device)
                epoch_loss += loss
            avg_loss = epoch_loss / TRAIN_STEPS_PER_EPOCH
            print(f"Average loss: {avg_loss:.4f}")

        torch.save(model.state_dict(), "dany_chess_trained.pth")
        print("Model saved.")

if __name__ == "__main__":
    main()
