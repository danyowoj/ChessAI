import torch
import chess

PIECE_TO_CHANNEL = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 2,
    chess.ROOK: 3,
    chess.QUEEN: 4,
    chess.KING: 5,
}

def board_to_tensor(board: chess.Board) -> torch.Tensor:
    """
    Кодирование шахматной позиции.
    Формирует тензор формы [18, 8, 8] с информацией:
    - фигуры (каналы 0-11)
    - очередь хода (12)
    - рокировки (13-14) с кодированием 1/3, 2/3, 1.0 для разных комбинаций
    - en passant (15)
    - halfmove clock (16)
    - fullmove number (17)
    """
    tensor = torch.zeros(18, 8, 8, dtype=torch.float32)

    # 1. Фигуры (каналы 0-11)
    for square, piece in board.piece_map().items():
        channel = PIECE_TO_CHANNEL[piece.piece_type]
        if piece.color == chess.BLACK:
            channel += 6
        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)
        tensor[channel, row, col] = 1.0

    # 2. Очередь хода (канал 12)
    if board.turn == chess.WHITE:
        tensor[12].fill_(1.0)

    # 3. Рокировки (каналы 13-14)
    # Белые
    castling_white = 0
    if board.has_kingside_castling_rights(chess.WHITE):
        castling_white += 1
    if board.has_queenside_castling_rights(chess.WHITE):
        castling_white += 2
    if castling_white > 0:
        tensor[13].fill_(castling_white / 3.0)  # значения: 1/3, 2/3 или 1.0

    # Чёрные
    castling_black = 0
    if board.has_kingside_castling_rights(chess.BLACK):
        castling_black += 1
    if board.has_queenside_castling_rights(chess.BLACK):
        castling_black += 2
    if castling_black > 0:
        tensor[14].fill_(castling_black / 3.0)

    # 4. En passant (канал 15)
    if board.ep_square is not None:
        row = 7 - chess.square_rank(board.ep_square)
        col = chess.square_file(board.ep_square)
        tensor[15, row, col] = 1.0

    # 5. Halfmove clock (канал 16)
    tensor[16].fill_(min(board.halfmove_clock / 100.0, 1.0))

    # 6. Fullmove number (канал 17)
    tensor[17].fill_(min(board.fullmove_number / 100.0, 1.0))

    return tensor
