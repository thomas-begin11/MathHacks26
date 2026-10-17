# Road Trip: Function Junction  -  a Strife! project (Python)
# Type a function, watch it plot live (like Desmos), then press Drive! and the
# car follows y = f(x) to the checkpoint without touching any obstacles.
#
# This file only wires the modules together. The real work lives in:
#   config.py     numbers + coordinate helpers (screen layout, speed, tolerances)
#   state.py      the shared game-state dictionary
#   mathparse.py  equation parser                  (role A: math / backend)
#   levels.py     level data                       (role B: levels / map)
#   ui.py         widgets: game page, menu page    (role C: UI)
#   draw.py       graph, obstacles, road, car      (role C: visuals)
#   game.py       rules, movement, crash / win     (roles A + B)
import sys

# Every module we own. Strife only re-runs this file on hot reload, so we forget the
# others here to make Python re-read them. ADD NEW MODULE NAMES TO THIS LIST.
MODULES = ("config", "state", "mathparse", "levels", "ui", "game", "draw")
for _m in MODULES:
    sys.modules.pop(_m, None)

import ui
import game
import draw

# Strife puts its API (UI, Page, Draw, ...) into this file's globals only, so hand it to the modules.
_API = {name: globals()[name] for name in
        ("UI", "Page", "Tween", "Storage", "Assets", "Input", "Draw", "After", "Overlaps", "Font", "Theme", "Quit")}
for _mod in (ui, game, draw):
    _mod.bind(_API)

ui.build({"drive": game.drive, "reset": game.reset, "next": game.next_level, "level": game.start_level})


def on_update(dt):
    if Page.Current() == "Game":
        game.update(dt)


def on_draw():
    if Page.Current() == "Game":
        draw.scene()
