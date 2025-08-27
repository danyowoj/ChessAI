import torch
from model import ChessNet
from data import fen_to_tensor, predict_uci_from_logits

MODEL_PATH = "chessnet.pth"

def load_model(path=MODEL_PATH, channels=64, depth=6, device=None):
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ChessNet(channels=channels, depth=depth).to(device)
    state = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(state)
    model.eval()
    return model, device

def best_move(fen: str, model=None, device=None) -> str:
    close_model = False
    if model is None:
        model, device = load_model()
        close_model = True
    x = fen_to_tensor(fen).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x)
    uci = predict_uci_from_logits(logits)
    if close_model:
        del model
    return uci

if __name__ == "__main__":
    # Проба на стартовой позиции
    fen0 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(best_move(fen0))