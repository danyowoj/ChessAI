$(document).ready(function () {
    var board = null;
    var game = new Chess();
    var $board = $('#board');
    var $status = $('#status');
    var $modal = $('#gameOverModal');
    var $gameResultText = $('#gameResultText');

    // Функция для обновления подсветки текущего игрока
    function updatePlayerHighlight() {
        $board.parent()
            .removeClass('white-turn black-turn')
            .addClass(game.turn() === 'w' ? 'white-turn' : 'black-turn');
    }

    // Функция для подсветки возможных ходов
    function highlightPossibleMoves(square) {
        // Очищаем предыдущие подсветки
        $board.find('.square-55d63').removeClass('highlight possible-move');

        // Подсвечиваем текущую клетку
        $board.find('.square-' + square).addClass('highlight');

        // Получаем возможные ходы
        var moves = game.moves({
            square: square,
            verbose: true
        });

        // Подсвечиваем возможные ходы
        moves.forEach(function (move) {
            $board.find('.square-' + move.to).addClass('possible-move');
        });
    }

    // Функция показа модального окна
    function showGameOverModal(message) {
        $gameResultText.text(message);
        $modal.css('display', 'flex');
    }

    // Функция скрытия модального окна
    function hideGameOverModal() {
        $modal.hide();
    }

    function updateStatus() {
        var moveColor = game.turn() === 'w' ? 'белых' : 'черных';

        if (game.in_checkmate()) {
            var winner = game.turn() === 'w' ? 'черных' : 'белых';
            $status.text('Мат. Победа ' + winner);
            showGameOverModal('Победа ' + winner + '!');
        } else if (game.in_draw()) {
            $status.text('Ничья');
            showGameOverModal('Ничья!');
        } else {
            $status.text('Ход ' + moveColor);
        }

        // Обновляем подсветку текущего игрока
        updatePlayerHighlight();
    }

    function onDragStart(source, piece) {
        if (game.game_over()) return false;

        // Проверка, чья фигура
        if ((game.turn() === 'w' && piece.startsWith('b')) ||
            (game.turn() === 'b' && piece.startsWith('w'))) {
            return false;
        }

        // Подсвечиваем возможные ходы
        highlightPossibleMoves(source);
    }

    function onDrop(source, target) {
        // Очищаем подсветку
        $board.find('.square-55d63').removeClass('highlight possible-move');

        var move = game.move({
            from: source,
            to: target,
            promotion: 'q'
        });

        if (move === null) return 'snapback';

        board.position(game.fen());
        updateStatus();
    }

    function onSnapEnd() {
        board.position(game.fen());
    }

    // Обработчик для кнопки рестарта
    $('#restartButton').click(function() {
        game.reset();
        board.start();
        $board.find('.square-55d63').removeClass('highlight possible-move');
        hideGameOverModal();
        updateStatus();
    });

    board = Chessboard('board', {
        draggable: true,
        position: 'start',
        pieceTheme: '/static/chessboard/img/chesspieces/wikipedia/{piece}.png',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onSnapEnd: onSnapEnd
    });

    // Инициализация подсветки
    updatePlayerHighlight();
    updateStatus();
});
