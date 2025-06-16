import os
from flask import Flask, render_template, request, jsonify
from stockfish import Stockfish

app = Flask(__name__)


# Определение пути к Stockfish
def get_stockfish_path():
    # Попробуем найти stockfish в разных местах
    paths = [
        os.path.join(os.path.dirname(__file__), 'bin', 'stockfish'),
        '/app/bin/stockfish',  # Для yhub.net
        '/usr/bin/stockfish',
        '/usr/games/stockfish',
        '/usr/local/bin/stockfish'
    ]

    for path in paths:
        if os.path.exists(path):
            return path

    return 'stockfish'  # Попробуем найти в PATH


try:
    stockfish_path = get_stockfish_path()
    print(f"Using Stockfish at: {stockfish_path}")
    stockfish = Stockfish(path=stockfish_path)
    stockfish.set_depth(15)
    stockfish.set_skill_level(20)
except Exception as e:
    print(f"Error initializing Stockfish: {str(e)}")
    stockfish = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/bestmove', methods=['POST'])
def bestmove():
    if not stockfish:
        return jsonify({'error': 'Stockfish not available'}), 500

    try:
        data = request.get_json()
        fen = data['fen']

        if not stockfish.is_fen_valid(fen):
            return jsonify({'error': 'Invalid FEN'}), 400

        stockfish.set_fen_position(fen)
        move = stockfish.get_best_move()

        if not move:
            return jsonify({'error': 'No move available'}), 400

        return jsonify({'bestmove': move})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
