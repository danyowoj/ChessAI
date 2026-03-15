import torch
import chess

def move_to_index(move: chess.Move) -> int:
    """Преобразование хода в индекс policy-вектора (0..4671)."""
    return move.from_square * 64 + move.to_square

def create_legal_move_mask(board: chess.Board, device=None) -> torch.Tensor:
    """
    Возвращает тензор [4672] с 1 на позициях легальных ходов, 0 на остальных.
    """
    mask = torch.zeros(4672, dtype=torch.float32, device=device)
    for move in board.legal_moves:
        idx = move_to_index(move)
        mask[idx] = 1.0
    return mask