# ChessAI

## Описание

**ChessAI** — это веб-приложение, позволяющее пользователю играть в шахматы против ИИ (движок **Stockfish**). Пользователь взаимодействует с шахматной доской через браузер, а Flask-сервер обрабатывает его ходы, отправляет их в Stockfish и возвращает ответ (лучший ход ИИ).


## Для пользователей

В проекте реализованы следующие моменты:
- **Игра против ИИ** — После завершения хода игрока ИИ автоматически начинает думать над своим ходом и совершает его.
- **Смена стороны** — Игрок может сменить сторону, нажав на кнопку _"Сменить сторону"_, выбирая между игрой за белые или черные фигуры.
- **Подсказки** — Кнопка _"Подсказка"_ позволяет получить рекомендацию по лучшему ходу от ИИ.
- **Сдача партии** — Кнопка _"Сдаться"_ позволяет сдать партию компьютеру и принять поражение.
- **Начало новой игры** — После завершения партии появляется кнопка _"Новая игра"_, которая позволяет начать новую игру.
- **Визуальные эффекты** — Реализована подсветка возможных ходов, при наведении на фигуру, и подсветка последнего хода.
- **Звуковые эффекты** — Реализован звук совершения хода.
- **Превращение пешки** — Когда пешка доходит до противоположного конца доски, есть возможность выбрать, в какую фигуру она превратится.

## Функциональность

- **Frontend**: HTML/CSS/JavaScript с использованием библиотек `Chessboard.js`, `Chess.js`, `jQuery`
- **Backend**: Flask-приложение (`app.py`)
- **ИИ**: интеграция Stockfish через UCI (подпроцесс)

## Ключевые функции

### Фронтенд (board.js):

| Функция               | Описание                                                                  |
| --------------------- | ------------------------------------------------------------------------- |
| `onDrop()`            | Обрабатывает перетаскивание и размещение фигур                            |
| `isPromotionMove()`   | Проверяет, достигла ли пешка противоположного края доски                  |
| `makeComputerMove()`  | Отправляет FEN на сервер и получает ход ИИ                                |
| `highlightLastMove()` | Подсвечивает последний ход                                                |
| `suggestMove()`       | Отправляет текущую позицию в Stockfish и подсвечивает рекомендованный ход |
| `switchSides()`       | Меняет цвет, за который играет пользователь                               |
| `updateStatus()`      | Обновляет информационную панель в UI                                      |

### Бэкенд (app.py):
| Эндпоинт    | Описание                                                  |
| ----------- | --------------------------------------------------------- |
| `/`         | Главная страница (рендерится `index.html`)                |
| `/playmove` | Принимает FEN, запускает Stockfish, возвращает лучший ход |

### Stockfish (через subprocess):
- Инициализируется один раз на каждый запрос
- Обрабатывает:
  - `position fen <...>`
  - `go depth 30`
- Возвращает `bestmove <...>`

## Основная логика

1. **Начало игры**
Пользователь открывает сайт, загружается 'index.html', 'style.css', 'board.js', и библиотеки 'chess.js' и 'chessboard.js.' По умолчанию пользователь играет белыми. Он может изменить сторону до первого хода.

2. **Ход игрока**
Пользователь перетаскивает фигуру (drag&drop). 'board.js' (функция 'onDrop') проверяет валидность хода (с помощью 'chess.js'). Если ход допустим, доска обновляется и вызывается 'makeComputerMove()'.

3. **Запрос к серверу**
'makeComputerMove()' отправляет POST-запрос на '/playmove' с текущим FEN (позиция доски). Flask-приложение ('app.py') принимает запрос, запускает subprocess Stockfish и передаёт ему позицию. Параметры Stockfish (установлены через 'setoption') — Threads=8, Hash=4096, go depth 30. Stockfish возвращает строку с 'bestmove'.

4. **Ответ от ИИ**
Flask обрабатывает 'bestmove' и отправляет его обратно клиенту. 'board.js' обновляет доску, подсвечивает последний ход, проигрывает звук.

## Системные требования

- ОС Linux
- Python 3.7+
- Современный браузер (Chrome, Firefox, Edge)
- Экран с разрешением ≥ 1024px
- Наличие интернета для загрузки фронтенд-зависимостей
- ~100 МБ дискового пространства и ~1 ГБ памяти

## Установка и развёртывание

1. Клонировать репозиторий:
```
git clone https://github.com/danyowoj/ChessAI.git
cd ChessAI
```
2. Создать виртуальное окружение (рекомуендуется):
```
python3 -m venv venv
source venv/bin/activate
```
3. Установить Python-зависимости:
```
pip install -r requirements.txt
```
4. Сделать бинарный файл Stockfish исполняемым:
```
chmod +x stockfish/stockfish-ubuntu-x86-64-avx2
```
5. Запустить Flask-сервер:
```
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
```
6. Открыть в браузере:
```
http://localhost:5000
```

## Планы по развитию

### Выбор уровня сложности
Реализуется через управление параметрами Stockfish:
| Уровень | Как задаётся   |
| ------- | ---------------|
| Лёгкий  | `go depth 5`   |
| Средний | `go depth 10`  |
| Сложный | `go depth 20+` |

### Дополнительные режими игры
| Режим                           | Особенности                               |
| ------------------------------- | ----------------------------------------- |
| Режим советника              | ИИ не играет, только подсказывает ходы       |
| Автоматические подсказки     | Автоотображение лучшего хода                 |
| Игра против другого человека | Без Stockfish, только взаимодействие клиента |
| Загрузка партии              | Импорт/экспорт PGN или FEN                   |
| Быстрые партии                | Ограничение времени на ход (таймер)         |
