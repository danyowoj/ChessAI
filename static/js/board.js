let board = null;
let game = new Chess();

function updateStatus() {
    const statusEl = document.getElementById('status');
    const moveColor = game.turn() === 'w' ? 'Ход белых' : 'Ход чёрных';
    statusEl.textContent = moveColor;
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
    // Подсвечивать только белые фигуры, когда их очередь
    if (!piece || piece[0] !== 'w' || game.turn() !== 'w') return;

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
    // - Не очередь белых
    // - Кликают по черной фигуре
    if (game.game_over() || game.turn() !== 'w' || piece[0] !== 'w') {
        return false;
    }
}

function onDrop(source, target) {
    removeGreySquares();

    const move = game.move({ from: source, to: target, promotion: 'q' });
    if (!move) return 'snapback';

    board.position(game.fen());
    updateStatus();

    // Если игра закончилась после хода белых, не запрашиваем ход черных
    if (game.game_over()) {
        showGameResult();
        return;
    }

     Задержка перед ходом черных
    setTimeout(() => {
        makeComputerMove();
    }, 300);
}

function makeComputerMove() {
    // Если уже не очередь черных (например, игра закончилась), не делаем ход
    if (game.game_over() || game.turn() !== 'b') return;

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

        const move = game.move(data.bestmove);
        if (!move) return;

        board.position(game.fen());
        updateStatus();

        // Проверяем, не закончилась ли игра после хода черных
        if (game.game_over()) {
            showGameResult();
        }
    })
    .catch(error => {
        console.error('Error making computer move:', error);
    });
}

function showGameResult() {
    let resultText = '';
    if (game.in_checkmate()) {
        resultText = game.turn() === 'w' ? 'Чёрные поставили мат! Поражение.' : 'Вы поставили мат! Победа!';
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

// Обновляем обработчик кнопки подсказки
$('#hintBtn').on('click', () => {
    if (game.game_over() || game.turn() !== 'w') return;

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
        greySquare(from);
        greySquare(to);
    })
    .catch(error => {
        console.error('Error getting hint:', error);
    });
});

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
    updateStatus();

    // Кнопка "сдаться"
    $('#resignBtn').on('click', () => $('#confirmResign').show());
    $('#confirmYes').on('click', () => {
        $('#confirmResign').hide();
        $('#resultText').text('Вы сдались. Поражение.');
        $('#resultModal').show();
    });
    $('#confirmNo').on('click', () => $('#confirmResign').hide());

    // Кнопка "подсказать ход"
    $('#hintBtn').on('click', () => {
        if (game.game_over() || game.turn() !== 'w') return;

        fetch('/bestmove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fen: game.fen() })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.bestmove) return;
            const from = data.bestmove.slice(0, 2);
            const to = data.bestmove.slice(2, 4);
            removeGreySquares();
            greySquare(from);
            greySquare(to);
        });
    });
});

window.addEventListener('resize', () => {
    if (board) board.resize();
});
