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
    Преобразует позицию python-chess в тензор [12, 8, 8]
    Каналы:
    0-5  — белые фигуры
    6-11 — черные фигуры
    """

    tensor = torch.zeros(12, 8, 8, dtype=torch.float32)

    for square, piece in board.piece_map().items():
        channel = PIECE_TO_CHANNEL[piece.piece_type]
        if piece.color == chess.BLACK:
            channel += 6

        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)

        tensor[channel, row, col] = 1.0

    return tensor
