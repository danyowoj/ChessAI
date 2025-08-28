import torch
import chess
from chessnet.model import ChessNet
from chessnet.data import fen_to_tensor, predict_uci_from_logits
import os

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "chessnet/chessnet.pth")

def load_model(path=MODEL_PATH, channels=64, depth=6, device=None):
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ChessNet(channels=channels, depth=depth).to(device)
    state = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(state)
    model.eval()
    return model, device

def best_move(fen: str, model=None, device=None, top_k: int = 20) -> str:
    """
    Возвращает легальный ход для данной позиции FEN.
    top_k — сколько лучших кандидатов рассматривать, если первый оказался нелегальным.
    """
    close_model = False
    if model is None:
        model, device = load_model()
        close_model = True

    # Прогон через сеть
    x = fen_to_tensor(fen).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(x)

    from_logits = logits[0, 0].reshape(-1)  # (64,)
    to_logits   = logits[0, 1].reshape(-1)  # (64,)

    # Получаем кандидатов: сортируем по вероятности
    from_probs = torch.softmax(from_logits, dim=0)
    to_probs   = torch.softmax(to_logits, dim=0)

    from_top = torch.argsort(from_probs, descending=True)[:top_k]
    to_top   = torch.argsort(to_probs, descending=True)[:top_k]

    board = chess.Board(fen)

    # Проверяем все комбинации кандидатов
    for fi in from_top:
        for ti in to_top:
            move = idx_to_square(fi.item()) + idx_to_square(ti.item())
            try:
                uci_move = chess.Move.from_uci(move)
            except:
                continue
            if uci_move in board.legal_moves:
                if close_model:
                    del model
                return move

    # Fallback: если ничего не подошло — берём первый легальный
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None  # Пат/мат
    return legal_moves[0].uci()

# вспомогательная функция
def idx_to_square(idx: int) -> str:
    r, c = divmod(idx, 8)
    file = chr(97 + c)
    rank = str(8 - r)
    return file + rank
