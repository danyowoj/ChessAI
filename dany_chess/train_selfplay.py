import torch
import torch.optim as optim
from dany_chess.model import AlphaZeroNet
from dany_chess.replay_buffer import ReplayBuffer
from dany_chess.trainer import train_step
from dany_chess.parallel_selfplay_gpu import parallel_selfplay_gpu

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 DEVICE: {device}")

    model = AlphaZeroNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=3e-5, weight_decay=1e-4)

    buffer = ReplayBuffer(max_size=200000)

    EPOCHS = 16
    GAMES_PER_EPOCH = 32
    SIMULATIONS = 500
    BATCH_EVAL_SIZE = 64
    BATCH_SIZE = 64
    TRAIN_STEPS_PER_EPOCH = 1000

    for epoch in range(EPOCHS):
        print(f"\n{'='*50}")
        print(f"🚀 EPOCH {epoch+1}/{EPOCHS}")
        print(f"{'='*50}")

        # Генерация игр
        print("🎮 Generating self-play games...")
        new_data = parallel_selfplay_gpu(
            model, device,
            num_games=GAMES_PER_EPOCH,
            simulations=SIMULATIONS,
            batch_size=BATCH_EVAL_SIZE,
            verbose=True
        )

        print(f"📦 Adding {len(new_data)} new positions to buffer...")
        for sample in new_data:
            buffer.add(sample)

        print(f"📊 Buffer size: {len(buffer)}")

        # Обучение
        if len(buffer) >= BATCH_SIZE:
            print(f"🧠 Training for {TRAIN_STEPS_PER_EPOCH} steps...")
            epoch_loss = 0.0
            for step in range(TRAIN_STEPS_PER_EPOCH):
                batch = buffer.sample(BATCH_SIZE)
                loss = train_step(model, optimizer, batch, device)
                epoch_loss += loss
                if (step+1) % 200 == 0:
                    print(f"  Step {step+1}/{TRAIN_STEPS_PER_EPOCH} | loss: {loss:.4f}")
            avg_loss = epoch_loss / TRAIN_STEPS_PER_EPOCH
            print(f"✅ Average loss: {avg_loss:.4f}")
        else:
            print("⚠️ Not enough data in buffer, skipping training.")

        # Сохранение модели
        torch.save(model.state_dict(), "../models/dany_chess_trained.pth")
        print("💾 Model saved.")

    print("\n🎉 Training finished!")

if __name__ == "__main__":
    main()
