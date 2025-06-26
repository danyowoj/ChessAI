from flask import Flask, render_template, request, jsonify
import chess
import chess.engine
import os
import subprocess

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


@app.route('/playmove', methods=['POST'])
def playmove():
    try:
        data = request.get_json()
        fen = data.get('fen')

        if not fen:
            return jsonify({'error': 'FEN not provided'}), 400

        # Запускаем Stockfish-процесс
        process = subprocess.Popen(
            [STOCKFISH_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True
        )

        def write(cmd):
            process.stdin.write(cmd + '\n')
            process.stdin.flush()

        def read_until(target):
            while True:
                line = process.stdout.readline()
                if line.strip().startswith(target):
                    return line.strip()

        # Инициализация и настройка параметров
        write("uci")
        read_until("uciok")

        write("setoption name Hash value 4096")
        write("setoption name Threads value 8")
        # write("setoption name UCI_LimitStrength value true")
        # write("setoption name UCI_Elo value 3190")

        write("isready")
        read_until("readyok")

        write("ucinewgame")
        write(f"position fen {fen}")
        write("isready")
        read_until("readyok")

        write("go depth 30")

        bestmove = None
        while True:
            line = process.stdout.readline().strip()
            if not line:
                continue

            print("SF:", line)  # Логировать для отладки

            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2 and len(parts[1]) == 4 or len(parts[1]) == 5:  # пример: e2e4 или e7e8q
                    bestmove = parts[1]
                else:
                    print("⚠️ Не удалось извлечь ход из строки:", line)
                break
        if not bestmove:
            return jsonify({'error': 'Stockfish не вернул ход'}), 500

        print("FEN на анализ:", fen)
        print(f"Stockfish выдал: {bestmove}")

        process.stdin.write("quit\n")
        process.stdin.flush()
        process.terminate()

        return jsonify({"bestmove": bestmove})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
