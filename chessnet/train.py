import time
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from datasets import load_dataset, logging

from model import ChessNet
from data import fen_to_tensor, uci_to_from_to

@dataclass
class Config:
    subset_fraction: float = 0.1     # доля датасета (0.01 = 1%)
    batch_size: int = 256
    lr: float = 1e-3
    epochs: int = 3
    channels: int = 64
    depth: int = 6
    num_workers: int = 2
    out_path: str = "chessnet.pth"
    amp: bool = True

def collate(batch):
    xs, from_idx, to_idx = [], [], []
    for b in batch:
        fen = b["fen"]
        line = b.get("line") or ""
        parts = line.split()
        if not fen or not parts:
            continue
        move = parts[0]
        x = fen_to_tensor(fen)
        f, t = uci_to_from_to(move)
        xs.append(x)
        from_idx.append(f)
        to_idx.append(t)

    if not xs:
        return None
    X = torch.stack(xs, 0)
    y_from = torch.tensor(from_idx, dtype=torch.long)
    y_to   = torch.tensor(to_idx,   dtype=torch.long)
    return X, y_from, y_to

def train(cfg: Optional[Config] = None):
    cfg = cfg or Config()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"✓ Используется устройство: {device}", end="")
    if device.type == "cuda":
        print(f" ({torch.cuda.get_device_name(0)})")
    else:
        print()

    logging.set_verbosity_info()
    print("→ Загружаем датасет HF...")
    t0 = time.perf_counter()

    ds_full = load_dataset("Lichess/chess-position-evaluations", split="train")
    ds = ds_full.select(range(int(cfg.subset_fraction * len(ds_full))))
    print(f"✓ Датасет загружен за {time.perf_counter() - t0:.1f} сек. "
        f"Размер: {len(ds)} примеров (из {len(ds_full)})")

    dl = DataLoader(
        ds,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
        collate_fn=collate,
        pin_memory=(device.type == "cuda")  # только если CUDA
    )

    model = ChessNet(channels=cfg.channels, depth=cfg.depth).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr)
    crit = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=(cfg.amp and device.type=="cuda"))

    for epoch in range(1, cfg.epochs+1):
        model.train()
        total, n = 0.0, 0
        pbar = tqdm(dl, desc=f"Epoch {epoch}/{cfg.epochs}")
        for batch in pbar:
            if batch is None: continue
            X, y_from, y_to = batch
            X, y_from, y_to = X.to(device), y_from.to(device), y_to.to(device)

            opt.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=(cfg.amp and device.type == "cuda")):
                logits = model(X)
                lf = crit(logits[:, 0].reshape(-1, 64), y_from)
                lt = crit(logits[:, 1].reshape(-1, 64), y_to)
                loss = lf + lt
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()

            total += loss.item()*X.size(0); n += X.size(0)
            pbar.set_postfix(loss=total/max(1,n))

        print(f"Epoch {epoch}: avg loss = {total/max(1,n):.4f}")

    torch.save(model.state_dict(), cfg.out_path)
    print(f"✓ Сохранено: {cfg.out_path}")

if __name__ == "__main__":
    train()
