"""Everything the player sees as widgets: the Game page, the Menu page, and small helpers
that other modules use to update them (set_msg, set_title, ...).

ui.py never imports game.py. Instead main.py passes in the functions the buttons should call.
"""
from levels import LEVELS
from config import W, H, GTOP, GBOT

UI = Page = Theme = None        # Strife's API; filled in by bind()


def bind(api):
    globals().update(api)


# widget handles, created by build()
title = readout = msg = inp = next_btn = None

MSG_COLORS = {"info": "#cfd8e3", "bad": "#ff8a8a", "good": "#8af08a"}


# ---------- helpers for other modules ----------
def set_msg(text, kind="info"):
    msg.text = text
    msg.color = MSG_COLORS[kind]


def set_title(text):
    title.text = text


def set_readout(text):
    readout.text = text


def show_next(visible):
    next_btn.visible = bool(visible)


def input_text():
    return inp.text


def clear_input():
    inp.text = ""


# ---------- building the pages ----------
def build(handlers):
    """handlers = dict of functions: drive(), reset(), next(), level(i)"""
    global title, readout, msg, inp, next_btn

    # Game page
    Page.Open("Game")
    top = UI.Frame(0, 0, W, GTOP)
    top.bg = "dark"
    title = UI.Text("", 16, 11, 26)
    title.color = "white"
    readout = UI.Text("", 520, 16, 20)
    readout.color = "#ffd25a"
    menu_btn = UI.Button("Menu", 840, 8, 110, 34)

    bottom = UI.Frame(0, GBOT, W, H - GBOT)
    bottom.bg = "panel"
    msg = UI.Text("", 16, 468, 18)
    ylab = UI.Text("y =", 16, 499, 26)
    ylab.color = "white"
    inp = UI.Input("type a function, e.g. 0.3x + 1", 62, 494, 480, 38)
    drive_btn = UI.Button("Drive!", 556, 494, 120, 38)
    reset_btn = UI.Button("Reset", 686, 494, 100, 38)
    next_btn = UI.Button("Next level", 796, 494, 148, 38)
    next_btn.visible = False

    Theme.Set("modern")
    for b, c in ((menu_btn, "#495057"), (drive_btn, "#2f9e44"), (reset_btn, "#868e96"), (next_btn, "#1971c2")):
        b.bg = c
        b.color = "white"

    menu_btn.on_click = lambda: Page.Open("Menu")
    drive_btn.on_click = handlers["drive"]
    inp.on_submit = lambda text: handlers["drive"]()
    reset_btn.on_click = handlers["reset"]
    next_btn.on_click = handlers["next"]

    # Menu page (opened last, so it is the first thing the player sees)
    Page.Open("Menu")
    UI.Text("Road Trip", 300, 50, 72).color = "#ffd25a"
    UI.Text("Function Junction", 330, 130, 36).color = "white"
    UI.Text("Drive the car to the flag by writing the road as a function, y = f(x).", 190, 190, 20).color = "#cfd8e3"
    for i, lv in enumerate(LEVELS):
        b = UI.Button(lv["name"] + "  -  " + lv["concept"], 250, 250 + i * 62, 460, 50)
        b.bg = "#1971c2"
        b.color = "white"
        b.on_click = (lambda n: lambda: handlers["level"](n))(i)
