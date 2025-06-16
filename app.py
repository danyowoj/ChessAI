from flask import Flask, render_template, request, jsonify
import chess
from stockfish import Stockfish

app = Flask(__name__)

stockfish = Stockfish(path="/usr/games/stockfish")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bestmove', methods=['POST'])
def bestmove():
    data = request.get_json()
    fen = data['fen']
    stockfish.set_fen_position(fen)
    move = stockfish.get_best_move()
    return jsonify({'bestmove': move})

if __name__ == '__main__':
    app.run(debug=True)
