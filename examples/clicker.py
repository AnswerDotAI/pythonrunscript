#!/usr/bin/env pythonrunscript
#
# Defines and serves an idleclicker game
#
# Just run me with pythonrunscript, and I will auto-install
# my dependencies and serve on port 8090
#
# ```requirements.txt
# python-fasthtml>=0.6.9,<0.7
# uvicorn>=0.29
# python-multipart
# sqlite-utils
# requests
# replicate
# pillow
# ```

from dataclasses import dataclass
from enum import Enum
from threading import Timer
import webbrowser, sys, copy

import uvicorn
from fasthtml.common import FastHTML, Div, P, Title, Main, Button, H1

####
#### define game logic
####

@dataclass
class GameState:
    money:int
    factories:int
    materials:int
    factory_price:int
    material_price:int
    material_needed_per_factory:int
    units_per_second:int

initial_state = GameState(90, 4, 5, 100, 10, 8, 4)
ACTIONS = Enum('ACTIONS',['PASS','BUY_FACTORY','BUY_MATERIAL'])

def print_game(state:GameState):
    state_dict = state.__dict__
    max_key_length = max(len(key) for key in state_dict)
    print("")
    for (key,value) in state_dict.items():
        print(f"    {key:<{max_key_length}}\t{value}")
    print("")

def evolve_state(starting_state, action):
    new_state = copy.copy(starting_state)
    if action == ACTIONS.PASS:
        new_state.money = new_state.money + new_state.factories
    elif action == ACTIONS.BUY_FACTORY:
        new_state.factories = new_state.factories + 1
        new_state.money = new_state.money - new_state.factory_price
        new_state.materials = new_state.materials - new_state.material_needed_per_factory
    elif action == ACTIONS.BUY_MATERIAL:
        new_state.money = new_state.money - new_state.material_price
        new_state.materials = new_state.materials + 1
    else:
        print("Error: unknown action")
    return new_state

####
#### define app
####

app = FastHTML()

# state
state = initial_state

def make_state_div():
    '''
    Returns a fresh state DIV reflecting game state
    '''
    return Div(P(f'Money: {state.money} '),
               P(f"Factories: {state.factories}"),
               P(f'Factory Price: {state.factory_price}'),
               P(f'Materials: {state.materials}'),
               P(f'Material Price: {state.material_price}'),
               P(f'Units Per Second: {state.units_per_second}'),
               id='state_div')

@app.get("/")
async def _():
    'Renders all UI'
    return (
        Title("Clicker Game"),
        Main(
            H1("hello world"),
            # Specifies that a click here will:
            # 1. will update #state_div element (hx_target='#state_div')
            # 2. by REPLACING it (hx_swap='outerHTML')
            # 3. with value returned by the function
            #    associated with /buyfactory route (hx_post='/buyfactory')
            Button('Buy Factory',
                   hx_post="/buyfactory",
                   hx_target='#state_div',
                   hx_swap="outerHTML"),
            Button('Buy Materials',
                   hx_post="/buymaterials",
                   hx_target='#state_div',
                   hx_swap="outerHTML"),
            make_state_div()))


@app.post("/buyfactory")
def _():
    'Handles a buy factory action, returns a fresh state div'
    global state
    action = ACTIONS.BUY_FACTORY
    state = evolve_state(state, action)
    return make_state_div()

@app.post("/buymaterials")
def _():
    global state
    action = ACTIONS.BUY_MATERIAL
    state = evolve_state(state, action)
    return make_state_div()

port=8090

def open_browser():
    url = f"http://localhost:{port}"
    print(f"Browsing to {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("--b"):
        Timer(1.5,open_browser).start()
    else:
        pass
    uvicorn.run(app, host="0.0.0.0", port=port)
    
