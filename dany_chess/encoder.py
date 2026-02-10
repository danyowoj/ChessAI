import torch
import chess


# Каналы фигур (0-11)
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
    Улучшеное кодирование шахматной позиции.

    Формирует тензор формы [18, 8, 8], содержащий:
    - фигуры
    - очередь хода
    - рокировки
    - en passant
    - halfmove и fullmove счетчики
    """

    tensor = torch.zeros(18, 8, 8, dtype=torch.float32)

    # === 1. Фигуры ===
    for square, piece in board.piece_map().items():
        channel = PIECE_TO_CHANNEL[piece.piece_type]
        if piece.color == chess.BLACK:
            channel += 6

        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)

        tensor[channel, row, col] = 1.0

    # === 2. Очередь хода ===
    # Если ходят белые, весь канал заполнен 1
    if board.turn == chess.WHITE:
        tensor[12].fill_(1.0)

    # === 3. Рокировка ===
    # Белые
    if board.has_kingside_castling_rights(chess.WHITE):
        tensor[13, :, :] =1.0
    if board.has_queenside_castling_rights(chess.WHITE):
        tensor[13, :, :] = 1.0

    # Черные
    if board.has_kingside_castling_rights(chess.BLACK):
        tensor[14, :, :] =1.0
    if board.has_queenside_castling_rights(chess.BLACK):
        tensor[14, :, :] = 1.0

    # === 4. En passant ===
    if board.ep_square is not None:
        row = 7 - chess.square_rank(board.ep_square)
        col = chess.square_file(board.ep_square)
        tensor[15, row, col] = 1.0

    # === 5. Halfmove clock ===
    tensor[16].fill_(min(board.halfmove_clock / 100.0, 1.0))

    # === 6. Fullmove number ===
    tensor[17].fill_(min(board.fullmove_number / 100.0, 1.0))

    return tensor
