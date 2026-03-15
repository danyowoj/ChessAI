import chess
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
        data = request.get_json()
        fen = data.get('fen')

        if not fen:
            return jsonify({'error': 'FEN not provided'}), 400

        # Валидация FEN
        try:
            board = chess.Board(fen)
        except ValueError as e:
            return jsonify({'error': f'Invalid FEN: {str(e)}'}), 400

        # Проверка, что игра не закончена
        if board.is_game_over():
            return jsonify({'error': 'Game is already over'}), 200

        # Небольшая случайная задержка
        delay = random.uniform(0.1, 1.0)
        time.sleep(delay)

        move = best_move(fen)

        if move is None:
            return jsonify({'error': 'Нет доступных ходов (мат или пат)'}), 200

        print(f"FEN: {fen} | AI move: {move.uci()} | delay: {delay:.3f}s")
        return jsonify({"bestmove": move.uci()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
