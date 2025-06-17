from flask import Flask, render_template, request, jsonify
from stockfish import Stockfish

app = Flask(__name__,
            static_folder='static',
            template_folder='.')

# Инициализация Stockfish с максимальными параметрами
try:
    # Инициализация Stockfish с совместимыми параметрами
    stockfish = Stockfish(
        path="/usr/games/stockfish",
        depth=22,
        parameters={
            "Threads": 4,  # Использовать 4 ядра
            "Hash": 2048,  # 2GB памяти
            "Skill Level": 20,  # Максимальная сложность (0-20)
            "UCI_LimitStrength": "false",
            "UCI_Elo": 3000,  # Максимальный рейтинг
            "Slow Mover": 100,  # Интенсивность анализа
            "Contempt": 0,  # Нейтральный стиль игры
            "Minimum Thinking Time": 1000  # Минимум 1 секунда на ход
        }
    )

    # Альтернативный способ включения NNUE (если доступен)
    if hasattr(stockfish, 'set_nnue'):
        stockfish.set_nnue("true")
        print("NNUE используется")

    print("Stockfish успешно инициализирован с параметрами:")
    print(stockfish.get_parameters())  # Выводим текущие параметры

except Exception as e:
    print(f"Ошибка инициализации Stockfish: {str(e)}")
    # Попробуем более простую инициализацию
    try:
        stockfish = Stockfish(path="stockfish")
        stockfish.set_depth(20)
        stockfish.set_skill_level(20)
        print("Использована упрощенная инициализация")
    except:
        print("Не удалось инициализировать Stockfish")
        exit(1)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/bestmove', methods=['POST'])
def bestmove():
    try:
        data = request.get_json()
        fen = data['fen']

        if not stockfish.is_fen_valid(fen):
            return jsonify({'error': 'Invalid FEN'}), 400

        stockfish.set_fen_position(fen)

        # Используем продвинутый метод с контролем времени
        move = stockfish.get_best_move_time(2000)  # 2 секунды на анализ

        if not move:
            return jsonify({'error': 'No move available'}), 400

        return jsonify({'bestmove': move})

    except Exception as e:
        print(f"Ошибка в bestmove: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    """Эндпоинт для динамического изменения сложности"""
    level = request.json.get('level', 'max')

    if level == 'easy':
        params = {"Skill Level": 5, "UCI_LimitStrength": "true", "UCI_Elo": 1200}
    elif level == 'medium':
        params = {"Skill Level": 15, "UCI_LimitStrength": "false"}
    else:  # max/hard
        params = {
            "Skill Level": 20,
            "UCI_LimitStrength": "false",
            "Threads": 4,
            "Hash": 2048
        }

    stockfish.update_engine_parameters(params)
    return jsonify({'status': f'Установлен уровень: {level}'})

if __name__ == '__main__':
    app.run(debug=True)
