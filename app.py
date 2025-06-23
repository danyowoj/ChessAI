from flask import Flask, render_template, request, jsonify
import chess
import chess.engine
import os

app = Flask(__name__, static_folder='static', template_folder='.')

# Путь к бинарному файлу Stockfish
STOCKFISH_PATH = os.path.join("stockfish", "stockfish-ubuntu-x86-64-avx2")  # Укажи свой путь здесь

try:
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    print("✅ Stockfish с NNUE запущен успешно.")
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

        # Максимально сильный вызов Stockfish: анализ на глубине 30
        limit = chess.engine.Limit(depth=30)  # или: Limit(time=5.0)
        result = engine.play(board, limit)

        move = result.move
        info = engine.analyse(board, limit)

        print(f"FEN: {fen}")
        print(f"Лучший ход: {move}")
        print(f"Оценка: {info.get('score')}")

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
