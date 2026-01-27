from flask import Flask, render_template, request, jsonify
import time
import random

from chess_ai import best_move

app = Flask(__name__, static_folder='static', template_folder='.')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/playmove', methods=['POST'])
def playmove():
    try:
        # Получаем данные от клиента
        data = request.get_json()
        fen = data.get('fen')

        if not fen:
            return jsonify({'error': 'FEN not provided'}), 400

        # Небольшая случайная задержка (имитация "размышления" ИИ)
        delay = random.uniform(0.1, 1.0)
        time.sleep(delay)

        # Получаем лучший ход от движка
        move = best_move(fen)

        if move is None:
            return jsonify({'error': 'Нет доступных ходов (мат или пат)'}), 200

        print(f"FEN: {fen} | AI move: {move.uci()} | delay: {delay:.3f}s")

        # Возвращаем ход в формате UCI
        return jsonify({"bestmove": move.uci()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
