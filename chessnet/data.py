from typing import Tuple, Optional
import torch
from datasets import load_dataset

PIECE_TO_CH = {'P':0,'N':1,'B':2,'R':3,'Q':4,'K':5,
               'p':6,'n':7,'b':8,'r':9,'q':10,'k':11}

def fen_to_tensor(fen: str) -> torch.Tensor:
    """
    FEN -> (12, 8, 8) битборды (только расположение фигур).
    Используем первую часть FEN (доска). Очередь хода можно учесть отдельным каналом при желании.
    """
    board = fen.split()[0]
    rows = board.split('/')
    t = torch.zeros(12, 8, 8, dtype=torch.float32)
    for r, row in enumerate(rows):
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                t[PIECE_TO_CH[ch], r, c] = 1.0
                c += 1
    return t

def uci_to_from_to(uci: str) -> Tuple[int, int]:
    """
    'e2e4' или 'a7a8q' -> индексы 0..63 для from/to (игнорируем промо-букву).
    """
    u = uci.strip()[:4]
    fx, fy = ord(u[0])-97, 8-int(u[1])
    tx, ty = ord(u[2])-97, 8-int(u[3])
    return fy*8+fx, ty*8+tx

def idx_to_square(idx: int) -> str:
    r, c = divmod(idx, 8)
    file = chr(97 + c)
    rank = str(8 - r)
    return file + rank

def predict_uci_from_logits(logits: torch.Tensor) -> str:
    """
    logits: (1,2,8,8) -> uci 'e2e4'
    """
    from_idx = torch.argmax(logits[0,0].reshape(-1)).item()
    to_idx   = torch.argmax(logits[0,1].reshape(-1)).item()
    return idx_to_square(from_idx) + idx_to_square(to_idx)

def load_lichess_eval(split: str = "train", subset: Optional[str] = None):
    """
    Загрузка датасета Lichess/chess-position-evaluations.
    Если subset задан, можно указать процент, например '[:0.5%]' для пробы.
    """
    hf_split = split + (subset or "")
    ds = load_dataset("Lichess/chess-position-evaluations", split=hf_split)
    return ds
