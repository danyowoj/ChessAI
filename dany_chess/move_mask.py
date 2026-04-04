import torch
import chess

def move_to_index(move: chess.Move) -> int:
    """
    Преобразование хода в индекс policy-вектора (0..4671).
    """
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

def transform_square(sq: int, transform_type) -> int:
    """
    Преобразует номер клетки (0-63) с учётом симметрии.
    transform_type: ('rotate', k) или ('reflect', axis)
    """
    row = sq // 8
    col = sq % 8

    if transform_type[0] == 'rotate':
        k = transform_type[1] % 4
        if k == 1:
            row, col = col, 7 - row
        elif k == 2:
            row, col = 7 - row, 7 - col
        elif k == 3:
            row, col = 7 - col, row
    elif transform_type[0] == 'reflect':
        axis = transform_type[1]
        if axis == 'h':
            row = 7 - row
        elif axis == 'v':
            col = 7 - col
        elif axis == 'd1':
            row, col = col, row
        elif axis == 'd2':
            row, col = 7 - col, 7 - row
    else:
        raise ValueError(f"Unknown transform type: {transform_type}")

    return row * 8 + col

def transform_move_index(idx: int, transform_type) -> int:
    """
    Преобразует индекс хода (from*64 + to) в соответствии с симметрией.
    transform_type: ('rotate', k) или ('reflect', axis)
    Возвращает новый индекс.
    """
    from_sq = idx // 64
    to_sq = idx % 64
    new_from = transform_square(from_sq, transform_type)
    new_to = transform_square(to_sq, transform_type)
    return new_from * 64 + new_to
