from flask import Flask, render_template, request, jsonify
from stockfish import Stockfish

app = Flask(__name__,
            static_folder='static',
            template_folder='.')

stockfish = Stockfish(path="/usr/games/stockfish")
stockfish.set_depth(20)
stockfish.set_skill_level(20)

if not stockfish._is_ready():
    print("Ошибка: Stockfish не готов!")
    # Попробуем альтернативный путь
    try:
        stockfish = Stockfish(path="stockfish")  # Попробовать путь по умолчанию
        print("Использован путь по умолчанию")
    except:
        print("Не удалось инициализировать Stockfish")
        exit(1)
else:
    print("Stockfish успешно инициализирован")

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/bestmove', methods=['POST'])
def bestmove():
    try:
        data = request.get_json()
        fen = data['fen']
        print(f"Получен FEN: {fen}")  # Логирование

        if not stockfish.is_fen_valid(fen):
            print("Неверный FEN")
            return jsonify({'error': 'Invalid FEN'}), 400

        stockfish.set_fen_position(fen)
        print("FEN установлен успешно")

        move = stockfish.get_best_move()
        print(f"Лучший ход: {move}")

        if not move:
            print("Stockfish не вернул ход")
            return jsonify({'error': 'No move available'}), 400

        return jsonify({'bestmove': move})

    except Exception as e:
        print(f"Ошибка в bestmove: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
