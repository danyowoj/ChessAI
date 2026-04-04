import torch
import chess
from dany_chess.move_mask import move_to_index, transform_move_index, transform_square

def transform_fen(fen: str, transform_type) -> str:
    """
    Преобразует FEN строку согласно симметрии.
    """
    board = chess.Board(fen)
    new_board = chess.Board()
    new_board.clear()
    # Переносим фигуры
    for square, piece in board.piece_map().items():
        new_sq = transform_square(square, transform_type)
        new_board.set_piece_at(new_sq, piece)
    # Очередь хода остаётся прежней
    new_board.turn = board.turn
    # Рокировки игнорируем для простоты (в обучении не критично)
    # Можно добавить преобразование, но для ускорения пропускаем
    return new_board.fen()

def get_all_symmetries(fen: str, policy: torch.Tensor):
    """
    Возвращает список из 8 кортежей (new_fen, new_policy).
    """
    transforms = [
        ('rotate', 0),
        ('rotate', 1),
        ('rotate', 2),
        ('rotate', 3),
        ('reflect', 'h'),
        ('reflect', 'v'),
        ('reflect', 'd1'),
        ('reflect', 'd2')
    ]
    results = []
    for t in transforms:
        new_fen = transform_fen(fen, t)
        new_policy = torch.zeros_like(policy)
        # Преобразуем только ненулевые индексы
        nonzero = policy.nonzero(as_tuple=True)[0]
        for idx in nonzero:
            new_idx = transform_move_index(idx.item(), t)
            new_policy[new_idx] = policy[idx]
        results.append((new_fen, new_policy))
    return results

def augment_data(data):
    """
    Принимает список кортежей (fen, policy, value).
    Возвращает расширенный список со всеми 8 симметриями для каждой позиции.
    """
    augmented = []
    for fen, policy, value in data:
        syms = get_all_symmetries(fen, policy)
        for sym_fen, sym_policy in syms:
            augmented.append((sym_fen, sym_policy, value))
    return augmented
