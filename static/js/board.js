let board = null;
let game = new Chess();
let pendingPromotion = null;
let playerColor = 'w';
let hasMoved = false;
const moveSound = new Audio('/static/sounds/move.mp3');
let lastMoveSquares = [];

function highlightLastMove(from, to) {
    // Удаляем предыдущую подсветку
    lastMoveSquares.forEach(sq => {
        $(`#board .square-${sq}`).removeClass('highlight-last');
    });

    // Очищаем массив
    lastMoveSquares = [];

    // Добавляем новые клетки
    if (from && to) {
        lastMoveSquares.push(from, to);
        $(`#board .square-${from}`).addClass('highlight-last');
        $(`#board .square-${to}`).addClass('highlight-last');
    }
}

function switchSides() {
    playerColor = (playerColor === 'w') ? 'b' : 'w';
    board.orientation(playerColor === 'w' ? 'white' : 'black');
    game.reset();
    board.start();
    highlightLastMove(null, null);
    updateStatus();
    hasMoved = false;
    $('#switchSidesBtn').show();

    if (game.turn() !== playerColor) {
        setTimeout(makeComputerMove, 300);
    }
}

function updateStatus() {
    const statusContainer = $('#statusContainer');
    const statusHeader = $('#statusHeader');
    const statusThinking = $('#statusThinking');

    statusContainer.addClass('hidden');

    if (game.turn() === playerColor) {
        // Ход игрока
        statusHeader.text(`Ваш ход (${playerColor === 'w' ? 'белые' : 'черные'})`);
        statusThinking.hide();

        // Обновляем классы для подсветки доски
        const boardElement = document.getElementById('board');
        boardElement.classList.remove('white-turn', 'black-turn');
        boardElement.classList.add(game.turn() === 'w' ? 'white-turn' : 'black-turn');
    } else {
        // Ход компьютера
        statusHeader.text('Компьютер думает');
        statusThinking.show();
    }

    statusContainer.removeClass('hidden');
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
    if (!piece || piece[0] !== playerColor || game.turn() !== playerColor) return;

    const moves = game.moves({ square, verbose: true });
    if (moves.length === 0) return;

    greySquare(square);
    moves.forEach(move => greySquare(move.to));
}


function onMouseoutSquare() {
    $('.square-55d63').not('.highlight-last').css('background', '');
}

function onDragStart(source, piece) {
    // Временно усиливаем подсветку при перетаскивании
    if (lastMoveSquares.includes(source)) {
        $(`#board .square-${source}`).css({
            'background-color': 'rgba(247, 198, 60, 0.9)',
            'box-shadow': 'inset 0 0 12px rgba(0, 0, 0, 0.5)'
        });
    }

    if (
        game.game_over() ||
        game.turn() !== playerColor ||
        piece[0] !== playerColor
    ) {
        return false;
    }
    //highlightLastMove(lastMoveSquares[0], lastMoveSquares[1]);
}

function onDrop(source, target) {
    removeGreySquares();
    $('.suggested-move').removeClass('suggested-move');

    // Восстанавливаем обычную подсветку
    if (lastMoveSquares.length === 2) {
        highlightLastMove(lastMoveSquares[0], lastMoveSquares[1]);
    }

    // Проверяем, является ли ход превращением пешки
    const promotionMove = isPromotionMove(source, target);

    if (promotionMove && game.turn() === playerColor) {
        pendingPromotion = { from: source, to: target };
        showPromotionModal();
        return 'snapback';
    } else if (promotionMove) {
        return completeMove(source, target, 'q');
    } else {
        return completeMove(source, target);
    }
}

function isPromotionMove(source, target) {
    const piece = game.get(source);
    if (!piece || piece.type !== 'p') return false;

    // Для белых пешек - 8-я горизонталь, для черных - 1-я
    return (piece.color === 'w' && target[1] === '8') ||
           (piece.color === 'b' && target[1] === '1');
}

function completeMove(source, target, promotion = 'q') {
    const move = game.move({
        from: source,
        to: target,
        promotion: promotion
    });

    if (!move) return 'snapback';

    board.position(game.fen());

    highlightLastMove(source, target);
    moveSound.play();

    updateStatus();

    if (game.game_over()) {
        showGameResult();
    } else if (game.turn() !== playerColor) {
        makeComputerMove();
    }

    if (!hasMoved) {
    $('#switchSidesBtn').hide();
    hasMoved = true;
    }

    return true;
}

function showPromotionModal() {
    $('#promotionModal').show();

    // Устанавливаем цвет фигур в зависимости от текущего игрока
    const color = game.turn() === 'w' ? 'w' : 'b';
    $('.promotion-piece').each(function() {
        const piece = $(this).data('piece');
        $(this).attr('src', `/static/chessboard/img/chesspieces/wikipedia/${color}${piece.toUpperCase()}.png`);
    });
}

// Обработчики выбора фигуры
$(document).ready(function() {
    $('.promotion-piece').on('click', function() {
        const piece = $(this).data('piece');
        $('#promotionModal').hide();

        if (pendingPromotion) {
            completeMove(pendingPromotion.from, pendingPromotion.to, piece);
            pendingPromotion = null;
        }
    });
});

async function makeComputerMove() {
    if (game.game_over() || game.turn() === playerColor) return;

    $('#computerThinking').show();

    try {
        updateStatus();

        console.log("Отправка FEN на сервер:", game.fen()); // Логирование

        const response = await fetch('/playmove', {
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

        const move = {
            from: data.bestmove.slice(0, 2),
            to: data.bestmove.slice(2, 4),
            promotion: data.bestmove.length === 5 ? data.bestmove[4] : undefined
        };

        const legalMove = game.move(move);
        if (!legalMove) {
            throw new Error("Сервер прислал недопустимый ход: " + data.bestmove);
        }


        board.position(game.fen());

        highlightLastMove(move.from, move.to);
        moveSound.play();

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
            game.turn(playerColor);
            updateStatus();
            alert("Компьютер не смог сделать ход. Ваш ход.");
        }
    } finally {
        $('#computerThinking').hide();
    }
}

function showGameResult() {
    let resultText = '';

    if (game.in_checkmate()) {
        // Если мат, и ходить должен игрок — он проиграл. Иначе — победил.
        resultText = game.turn() === playerColor
            ? 'Компьютер поставил мат! Вы проиграли.'
            : 'Вы поставили мат! Победа!';
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

async function suggestMove() {
    if (game.game_over() || game.turn() !== playerColor) return;

    $('#statusHeader').text('Формирование подсказки');
    $('#statusAnalysis').html('<div class="thinking-dots active"><div class="thinking-dot"></div><div class="thinking-dot"></div><div class="thinking-dot"></div></div>');
    $('#statusThinking').show();

    try {
        const response = await fetch('/playmove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fen: game.fen() })
        });

        if (!response.ok) throw new Error('Ошибка сервера');

        const data = await response.json();
        if (!data.bestmove) throw new Error('Подсказка не найдена');

        const from = data.bestmove.slice(0, 2);
        const to = data.bestmove.slice(2, 4);

        // Форматируем подсказку
        const moveNotation = game.move({
            from: from,
            to: to,
            promotion: data.bestmove.length === 5 ? data.bestmove[4] : undefined
        }).san;

        // Отображаем подсказку
        $('#statusHeader').text('Рекомендованный ход');
        $('#statusAnalysis').html(`
            <div>${moveNotation}</div>
            <div class="suggestion-text">Нажмите на фигуру, чтобы увидеть возможные ходы</div>
        `);

        // Подсвечиваем ход на доске
        removeGreySquares();
        $(`#board .square-${from}`).css('background', '#00ff0060');
        $(`#board .square-${to}`).css('background', '#00ff0060');

    } catch (error) {
        console.error('Ошибка получения подсказки:', error);
        $('#statusHeader').text('Не удалось сформировать подсказку');
        $('#statusThinking').hide();

        // Восстанавливаем обычный статус через 2 секунды
        setTimeout(() => {
            updateStatus();
        }, 2000);
    } finally {
        $('#statusThinking').hide();
    }
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

    // Кнопка "Сменить сторону"
    $('#switchSidesBtn').on('click', () => {
        $('#confirmSwitch').show();
    });

    // Кнопки подтверждения смены
    $('#confirmSwitchYes').on('click', () => {
        $('#confirmSwitch').hide();
        switchSides(); // выполняем смену
    });

    $('#confirmSwitchNo').on('click', () => {
        $('#confirmSwitch').hide(); // отмена
    });

    // Кнопка "предложить ход"
    $('#suggestBtn').on('click', suggestMove);
});

window.addEventListener('resize', () => {
    if (board) board.resize();
});