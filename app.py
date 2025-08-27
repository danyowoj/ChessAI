from flask import Flask, render_template, request, jsonify
import torch
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

        move = best_move(fen, model, device)
        print(f"FEN: {fen} | AI move: {move}")
        return jsonify({"bestmove": move})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
