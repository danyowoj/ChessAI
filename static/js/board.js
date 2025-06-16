let board = null;
let game = new Chess();

function updateStatus() {
    const statusEl = document.getElementById('status');
    statusEl.textContent = game.turn() === 'w' ? 'Ваш ход (белые)' : 'Компьютер думает...';

    // Подсветка текущего игрока
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
    // Подсвечивать только белые фигуры, когда ход белых
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
    $('.suggested-move').removeClass('suggested-move');

    try {
        const move = game.move({
            from: source,
            to: target,
            promotion: 'q' // Всегда превращаем в ферзя для простоты
        });

        if (!move) {
            console.log("Недопустимый ход игрока");
            return 'snapback';
        }

        board.position(game.fen());
        updateStatus();

        if (game.game_over()) {
            showGameResult();
            return;
        }

        // Делаем ход компьютера через небольшую задержку
        setTimeout(makeComputerMove, 100);

    } catch (e) {
        console.error("Ошибка при ходе игрока:", e);
        return 'snapback';
    }
}

async function makeComputerMove() {
    if (game.game_over()) return;
    if (game.turn() !== 'b') return; // Проверяем, что сейчас ход чёрных (компьютера)

    try {
        updateStatus(); // Показываем "Компьютер думает..."

        console.log("Отправка FEN на сервер:", game.fen()); // Логирование

        const response = await fetch('/bestmove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fen: game.fen() })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Ответ сервера:", data); // Логирование

        if (!data.bestmove) {
            throw new Error("Сервер не вернул ход");
        }

        const move = game.move(data.bestmove);
        if (!move) {
            throw new Error("Недопустимый ход");
        }

        board.position(game.fen());
        updateStatus();

        if (game.game_over()) {
            showGameResult();
        }
    } catch (error) {
        console.error("Ошибка при ходе компьютера:", error);

        // В случае ошибки пробуем сделать случайный ход
        try {
            const moves = game.moves();
            if (moves.length > 0) {
                const randomMove = moves[Math.floor(Math.random() * moves.length)];
                game.move(randomMove);
                board.position(game.fen());
                updateStatus();
                console.log("Компьютер сделал случайный ход:", randomMove);
            } else {
                throw new Error("Нет доступных ходов");
            }
        } catch (fallbackError) {
            console.error("Ошибка при случайном ходе:", fallbackError);
            // Если даже случайный ход не получился, передаём ход игроку
            game.turn('w');
            updateStatus();
            alert("Компьютер не смог сделать ход. Ваш ход.");
        }
    }
}

function showGameResult() {
    let resultText = '';
    if (game.in_checkmate()) {
        resultText = game.turn() === 'w' ? 'Компьютер поставил мат! Вы проиграли.' : 'Вы поставили мат! Победа!';
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
    // Проверяем доступность сервера при загрузке
    fetch('/')
        .then(response => {
            if (!response.ok) throw new Error("Сервер не отвечает");
            console.log("Соединение с сервером установлено");
        })
        .catch(error => {
            console.error("Ошибка соединения:", error);
            alert("Ошибка соединения с сервером. Игра может работать некорректно.");
        });

    // Инициализация доски
    board = Chessboard('board', config);
    board.start();
    updateStatus();

    // Кнопка "сдаться"
    $('#resignBtn').on('click', () => $('#confirmResign').show());
    $('#confirmYes').on('click', () => {
        $('#confirmResign').hide();
        $('#resultText').text('Вы сдались. Победа компьютера!');
        $('#resultModal').show();
    });
    $('#confirmNo').on('click', () => $('#confirmResign').hide());

    // Кнопка "предложить ход"
    $('#suggestBtn').on('click', suggestMove);
});

window.addEventListener('resize', () => {
    if (board) board.resize();
});
