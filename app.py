from flask import Flask, render_template, request, jsonify
import torch
import time, random

from chess_ai import best_move, load_model

app = Flask(__name__, static_folder='static', template_folder='.')

# Загружаем модель один раз при старте
model, device = load_model()

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

        # Случайная задержка 100–1000 мс
        delay = random.uniform(0.1, 1.0)
        time.sleep(delay)

        move = best_move(fen, model, device)
        if move is None:
            return jsonify({'error': 'Нет доступных ходов (мат или пат)'}), 200

        print(f"FEN: {fen} | AI move: {move} | delay: {delay:.3f}s")
        return jsonify({"bestmove": move})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
