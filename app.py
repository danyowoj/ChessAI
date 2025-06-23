from flask import Flask, render_template, request, jsonify
import chess
import chess.engine
import os

app = Flask(__name__, static_folder='static', template_folder='.')

# Путь к бинарнику (должен быть с NNUE и AVX2!)
STOCKFISH_PATH = os.path.join("stockfish", "stockfish-ubuntu-x86-64-avx2")

try:
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    engine.configure({
        "Threads": 4,
        "Hash": 2048
    })
    print("✅ Stockfish запущен с NNUE и оптимальными параметрами.")
except Exception as e:
    print(f"❌ Ошибка запуска Stockfish: {e}")
    engine = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bestmove', methods=['POST'])
def bestmove():
    try:
        data = request.get_json()
        fen = data.get('fen')
        if not fen:
            return jsonify({'error': 'FEN not provided'}), 400

        board = chess.Board(fen)
        if board.is_game_over():
            return jsonify({'error': 'Game already over'}), 400

        # Выставляем глубокий анализ
        limit = chess.engine.Limit(depth=35)  # Или time=10.0
        result = engine.play(board, limit)

        move = result.move

        print(f"FEN: {fen}")
        print(f"Best move: {move}")

        return jsonify({'bestmove': move.uci()})

    except Exception as e:
        print(f"Ошибка при анализе хода: {e}")
        return jsonify({'error': str(e)}), 500

@app.teardown_appcontext
def shutdown_engine(exception=None):
    if engine:
        engine.quit()

if __name__ == "__main__":
    app.run(debug=True)
