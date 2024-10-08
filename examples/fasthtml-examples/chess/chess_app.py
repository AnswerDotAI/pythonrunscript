#!/usr/bin/env pythonrunscript
# /// pythonrunscript-requirements-txt
# python-fasthtml>=0.6.9,<0.7
# chess
# ///


# AUTOGENERATED! DO NOT EDIT! File to edit: chess_app.ipynb.

# %% auto 0
__all__ = ['cboard', 'css', 'gridlink', 'htmx_ws', 'app', 'rt', 'player_queue', 'ROWS', 'COLS', 'WS', 'Board', 'Home', 'get',
           'post', 'put']

# %% chess_app.ipynb 4
#from fasthtml import *
from fasthtml.common import *
from fastcore.utils import *
from fastcore.xml import to_xml
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute

import chess
import chess.svg

cboard = chess.Board()
# move e2e4
cboard.push_san('e4')
cboard.push_san('e5')
css = Style(
    '''\
    #chess-board { display: grid; grid-template-columns: repeat(8, 64px); grid-template-rows: repeat(8, 64px);gap: 1px; }
    .board-cell { width: 64px; height: 64px; border: 1px solid black; }
    .black { background-color: grey; }
    .white { background-color: white; }
    .active { background-color: green; }
    '''
)
# Flexbox CSS (http://flexboxgrid.com/)
gridlink = Link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css", type="text/css")
htmx_ws = Script(src="https://unpkg.com/htmx-ext-ws@2.0.0/ws.js")

app = FastHTML(hdrs=(gridlink, css, htmx_ws,))
rt = app.route

# %% chess_app.ipynb 5
player_queue = []
class WS(WebSocketEndpoint):
    encoding = 'text'

    async def on_connect(self, websocket):
        global player_queue
        player_queue.append(websocket)
        await websocket.accept()
        print(f'There are {len(player_queue)} players in the queue')
        await websocket.send_text("<div id='user-message'>Hello, you connected!</div>")
        if len(player_queue) == 2:
            await player_queue[0].send_text("<div id='user-message'>Opponent joined! Let the game begin!</div>")
            await player_queue[1].send_text("<div id='user-message'>You joined! Let the game begin!</div>")

    async def on_receive(self, websocket, data):
        await websocket.send_text("hi")

    async def on_disconnect(self, websocket, close_code):
        global player_queue
        player_queue.remove(websocket)
        for player in player_queue:
            await player.send_text("<div id='user-message'>Opponent disconnected!</div>")

app.routes.append(WebSocketRoute('/chess', WS))

# %% chess_app.ipynb 6
ROWS = '87654321'
COLS = 'abcdefgh'
def Board(lmoves: list[str] = [], selected: str = ''):
    board = []
    for row in ROWS:
        board_row = []
        for col in COLS:
            pos = f"{col}{row}"
            cell_color = "black" if (ROWS.index(row) + COLS.index(col)) % 2 == 0 else "white"
            cell_color = 'active' if pos in lmoves else cell_color
            cell_cls = f'board-cell {cell_color}'
            if pos == selected:
                cell_cls += ' selected'
            piece = cboard.piece_at(chess.parse_square(pos))
            if piece:
                piece = NotStr(chess.svg.piece(piece))
                board_row.append(
                    Div(
                        piece, id=pos, cls=cell_cls, hx_post="/select", hx_vals={'col': col, 'row': row},
                        hx_swap='outerHTML', hx_target='#chess-board', hx_trigger='click'
                    )
                )
            else:
                cell = Div(id=pos, cls=cell_cls)
                if selected != '':
                    move = f'{selected}{pos}'
                    print(move)
                    if chess.Move.from_uci(move) in cboard.legal_moves:
                        cell = Div(id=pos, cls=cell_cls, hx_put="/move", hx_vals={'move': move},
                            hx_swap='outerHTML', hx_target='#chess-board', hx_trigger='click'
                        )
                board_row.append(cell)
        board.append(Div(*board_row, cls="board-row"))
    return Div(*board, id="chess-board")

# %% chess_app.ipynb 7
def Home():
    return Div(
        Div('Hello, still waiting on an opponent!', id='user-message'),
        Board(),
        hx_ext="ws", ws_connect="/chess"
    )

# %% chess_app.ipynb 8
@rt("/")
def get():
    return Home()

# %% chess_app.ipynb 9
@rt('/select')
async def post(col: str, row: str):
    global cboards
    lmoves = []
    for m in cboard.legal_moves:
        if str(m).startswith(f'{col}{row}'):
            lmoves.append(str(m)[2:])
    return Board(lmoves=lmoves, selected=f'{col}{row}')

# %% chess_app.ipynb 10
@rt('/move')
async def put(move: str):
    global cboards
    cboard.push_san(move)
    for player in player_queue:
        await player.send_text(to_xml(Board()))


from fasthtml.common import serve

serve()