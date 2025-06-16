let board = null;
let game = new Chess();

function updateStatus() {
    const statusEl = document.getElementById('status');
    const moveColor = game.turn() === 'w' ? 'Ход белых' : 'Ход чёрных';
    statusEl.textContent = moveColor;
    
    // Обновляем подсветку текущего игрока
    const boardElement = document.getElementById('board');
    boardElement.classList.remove('white-turn', 'black-turn');
    boardElement.classList.add(game.turn() === 'w' ? 'white-turn' : 'black-turn');
}

function removeGreySquares() {
    $('#board .square-55d63').css('background', '');
}

function greySquare(square) {
    const $square = $('#board .square-' + square);
    const background = $square.hasClass('black-3c85d') ? '#696969' : '#a9a9a9';
    $square.css('background', background);
}

function onMouseoverSquare(square, piece) {
    // Подсвечивать только фигуры текущего игрока
    if (!piece || piece[0] !== game.turn()) return;

    const moves = game.moves({ square, verbose: true });
    if (moves.length === 0) return;

    greySquare(square);
    moves.forEach(move => greySquare(move.to));
}

function onMouseoutSquare() {
    removeGreySquares();
}

function onDragStart(source, piece) {
    // Запретить перетаскивание, если:
    // - Игра закончена
    // - Не очередь текущего игрока
    if (game.game_over() || piece[0] !== game.turn()) {
        return false;
    }
}

function onDrop(source, target) {
    removeGreySquares();
    $('.suggested-move').removeClass('suggested-move');

    const move = game.move({ from: source, to: target, promotion: 'q' });
    if (!move) return 'snapback';

    board.position(game.fen());
    updateStatus();

    if (game.game_over()) {
        showGameResult();
    }
}

function showGameResult() {
    let resultText = '';
    if (game.in_checkmate()) {
        resultText = game.turn() === 'w' ? 'Чёрные поставили мат! Победа чёрных.' : 'Белые поставили мат! Победа белых!';
    } else if (game.in_draw()) {
        resultText = 'Игра закончилась вничью.';
    } else if (game.in_stalemate()) {
        resultText = 'Пат. Ничья.';
    } else if (game.in_threefold_repetition()) {
        resultText = 'Ничья по троекратному повторению.';
    } else if (game.insufficient_material()) {
        resultText = 'Ничья из-за недостатка материала.';
    }

    if (resultText) {
        $('#resultText').text(resultText);
        $('#resultModal').show();
    }
}

function suggestMove() {
    if (game.game_over()) return;

    fetch('/bestmove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fen: game.fen() })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (!data.bestmove) return;

        const from = data.bestmove.slice(0, 2);
        const to = data.bestmove.slice(2, 4);

        removeGreySquares();
        $(`#board .square-${from}`).addClass('suggested-move');
        $(`#board .square-${to}`).addClass('suggested-move');
    })
    .catch(error => {
        console.error('Error getting suggested move:', error);
    });
}

const config = {
    draggable: true,
    position: 'start',
    pieceTheme: '/static/chessboard/img/chesspieces/wikipedia/{piece}.png',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onMouseoutSquare: onMouseoutSquare,
    onMouseoverSquare: onMouseoverSquare
};

$(document).ready(function () {
    board = Chessboard('board', config);
    board.start();
    updateStatus();

    // Кнопка "сдаться"
    $('#resignBtn').on('click', () => $('#confirmResign').show());
    $('#confirmYes').on('click', () => {
        $('#confirmResign').hide();
        const loser = game.turn() === 'w' ? 'Белые' : 'Чёрные';
        const winner = game.turn() === 'w' ? 'Чёрные' : 'Белые';
        $('#resultText').text(`${loser} сдались. ${winner} победили!`);
        $('#resultModal').show();
    });
    $('#confirmNo').on('click', () => $('#confirmResign').hide());

    // Кнопка "предложить ход"
    $('#suggestBtn').on('click', suggestMove);
});

window.addEventListener('resize', () => {
    if (board) board.resize();
});
