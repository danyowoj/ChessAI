import torch
import torch.optim as optim
import os
import shutil
from dany_chess.model import AlphaZeroNet
from dany_chess.replay_buffer import ReplayBuffer
from dany_chess.trainer import train_step
from dany_chess.parallel_selfplay_gpu import parallel_selfplay_gpu
from dany_chess.augmentation import augment_data

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 DEVICE: {device}")

    # Модель с 12 residual блоками и 256 фильтрами
    model = AlphaZeroNet(in_channels=18, num_blocks=12, filters=256).to(device)
    model_path = "dany_chess_trained.pth"

    if os.path.exists(model_path):
        print(f"⚠️ Found existing model at {model_path}. Attempting to load...")
        try:
            model.load_state_dict(torch.load(model_path, map_location=device))
            print("✅ Model loaded successfully.")
        except RuntimeError as e:
            print(f"❌ Failed to load model: {e}")
            print("🔄 Renaming old model and starting from random initialization.")
            backup_path = model_path + ".incompatible"
            shutil.move(model_path, backup_path)
            print(f"   Old model moved to {backup_path}")
    else:
        print("⚠️ No saved model found, starting from random initialization.")

    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    buffer = ReplayBuffer(max_size=500000)

    # Гиперпараметры
    EPOCHS = 100 #500
    GAMES_PER_EPOCH = 32 #128
    SIMULATIONS = 800
    BATCH_EVAL_SIZE = 128
    BATCH_SIZE = 128
    TRAIN_STEPS_PER_EPOCH = 2000

    for epoch in range(EPOCHS):
        print(f"\n{'='*50}")
        print(f"🚀 EPOCH {epoch+1}/{EPOCHS}")
        print(f"{'='*50}")

        print("🎮 Generating self-play games...")
        new_data = parallel_selfplay_gpu(
            model, device,
            num_games=GAMES_PER_EPOCH,
            simulations=SIMULATIONS,
            batch_size=BATCH_EVAL_SIZE,
            verbose=True
        )

        print(f"📦 Augmenting data (8x)...")
        augmented_data = augment_data(new_data)
        print(f"   Original: {len(new_data)} positions -> Augmented: {len(augmented_data)} positions")

        for sample in augmented_data:
            buffer.add(sample)

        print(f"📊 Buffer size: {len(buffer)}")

        if len(buffer) >= BATCH_SIZE:
            print(f"🧠 Training for {TRAIN_STEPS_PER_EPOCH} steps...")
            epoch_loss = 0.0
            for step in range(TRAIN_STEPS_PER_EPOCH):
                batch = buffer.sample(BATCH_SIZE)
                loss = train_step(model, optimizer, batch, device)
                epoch_loss += loss
                if (step+1) % 1000 == 0:
                    print(f"  Step {step+1}/{TRAIN_STEPS_PER_EPOCH} | loss: {loss:.4f}")
            avg_loss = epoch_loss / TRAIN_STEPS_PER_EPOCH
            print(f"✅ Average loss: {avg_loss:.4f}")
            scheduler.step(avg_loss)
            current_lr = optimizer.param_groups[0]['lr']
            print(f"Learning rate: {current_lr:.2e}")
        else:
            print("⚠️ Not enough data in buffer, skipping training.")

        torch.save(model.state_dict(), model_path)
        print("💾 Model saved.")

    print("\n🎉 Training finished!")

if __name__ == "__main__":
    main()
