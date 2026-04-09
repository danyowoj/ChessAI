import torch
import torch.optim as optim
from dany_chess.model import AlphaZeroNet
from dany_chess.external_dataset import ChessAlphaDataset
from dany_chess.trainer import train_step

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 DEVICE: {device}")

    # Создаём модель (архитектура должна совпадать с той, что будет использоваться в self-play)
    model = AlphaZeroNet(in_channels=18, num_blocks=12, filters=256).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)

    # Загружаем датасет (можно ограничить количество примеров для теста)
    dataset = ChessAlphaDataset(split='train', max_samples=1280)  # max_samples=None
    batch_size = 128
    num_epochs = 10   # для предобучения достаточно 5-10 эпох

    # Индексы для батчей
    num_samples = len(dataset)
    indices = list(range(num_samples))

    print(f"Starting pretraining")
    for epoch in range(num_epochs):
        print(f"Epoch {epoch + 1}/{num_epochs} ...")
        # Перемешиваем индексы
        torch.manual_seed(epoch)
        shuffled = torch.randperm(num_samples).tolist()
        total_loss = 0.0
        num_batches = 0

        for start in range(0, num_samples, batch_size):
            batch_indices = shuffled[start:start+batch_size]
            # Формируем батч
            states, policies, values = dataset.get_batch(batch_indices)
            # Упаковываем в список кортежей для совместимости с train_step
            batch = list(zip(states, policies, values))
            loss = train_step(model, optimizer, batch, device, use_fen=False)
            total_loss += loss
            num_batches += 1

            if num_batches % 100 == 0:
                print(f"Epoch {epoch+1}, batch {num_batches}, loss: {loss:.4f}")

        avg_loss = total_loss / num_batches
        print(f"Epoch {epoch+1}/{num_epochs} finished. Average loss: {avg_loss:.4f}")

        # Сохраняем модель после каждой эпохи
        torch.save(model.state_dict(), "dany_chess_pretrained.pth")
        print("Model saved as dany_chess_pretrained.pth")

    print("✅ Pretraining completed!")

if __name__ == "__main__":
    main()
