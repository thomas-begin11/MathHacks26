# Road Trip: Function Junction  -  a Strife! project (Python)
# Type a function, watch it plot live (like Desmos), then press Drive! and the
# car follows y = f(x) to the checkpoint without touching any obstacles.
#
# Files:  mathparse.py = equation parser   levels.py = level data   main.py = game
import math
import sys
for _m in ("mathparse", "levels"):      # so hot reload picks up edits to those files too
    sys.modules.pop(_m, None)
from mathparse import parse, safe_eval
from levels import LEVELS

# ---------- graph geometry (pixels <-> graph units) ----------
W, H = 960, 540
GTOP, GBOT = 50, 460            # the graph occupies y = 50..460 on screen
SCALE = 60                      # pixels per graph unit
OX, OY = 60, 420                # screen position of graph point (0, 0)
SPEED = 4.0                     # car speed, graph units per second
TOL = 0.35                      # how close to the flag counts as reaching it
START_TOL = 0.3                 # how close the road must pass to the car's start


def to_px(x, y):
    return OX + x * SCALE, OY - y * SCALE


def to_x(px):
    return (px - OX) / SCALE


# ---------- game state ----------
S = dict(level=0, f=None, text="", err="", mode="edit", cx=0.0, cy=0.0, crash=None, ys=[], msg="", kind="info", pan=None, mouse_down=False)


def set_msg(text, kind="info"):
    S["msg"], S["kind"] = text, kind
    msg.text = text
    msg.color = {"info": "#cfd8e3", "bad": "#ff8a8a", "good": "#8af08a"}[kind]


# ---------- Game page  (Function Junction) ----------
Page.Open("GameFJ")
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
for _b, _c in ((menu_btn, "#495057"), (drive_btn, "#2f9e44"), (reset_btn, "#868e96"), (next_btn, "#1971c2")):
    _b.bg = _c
    _b.color = "white"


# Bomb Defusal has its own page and Lua implementation in scripts/main.lua.


# ---------- Menu page ----------
Page.Open("Menu")
UI.Text("Road Trip", 300, 50, 72).color = "#ffd25a"
UI.Text("Choose a game mode", 330, 145, 30).color = "white"
fj_mode_btn = UI.Button("Function Junction", 250, 220, 460, 64)
fj_mode_btn.bg = "#1971c2"
fj_mode_btn.color = "white"
fj_mode_btn.on_click = lambda: Page.Open("FunctionJunctionMenu")

bd_mode_btn = UI.Button("Bomb Defusal", 250, 310, 460, 64)
bd_mode_btn.bg = "#c92a2a"
bd_mode_btn.color = "white"
bd_mode_btn.on_click = lambda: Page.Open("GameBD")

Page.Open("Menu")


# ---------- Function Junction level-select page ----------
Page.Open("FunctionJunctionMenu")
UI.Text("Function Junction", 300, 50, 48).color = "#ffd25a"
UI.Text("Choose a level: write y = f(x) to guide the car.", 230, 125, 20).color = "#cfd8e3"
for i, lv in enumerate(LEVELS):
    b = UI.Button(lv["name"] + "  -  " + lv["concept"], 250, 190 + i * 54, 460, 44)
    b.bg = "#1971c2"
    b.color = "white"
    b.on_click = (lambda n: lambda: start_level(n))(i)

fj_back_btn = UI.Button("Back to modes", 30, 474, 150, 42)
fj_back_btn.bg = "#495057"
fj_back_btn.color = "white"
fj_back_btn.on_click = lambda: Page.Open("Menu")

def layout_window():
    """Keep the Function Junction UI positioned for Strife's fixed 960x540 window."""
    top.w = W
    bottom.w, bottom.y, bottom.h = W, GBOT, H - GBOT
    readout.x = 520
    menu_btn.x = 840
    msg.y, ylab.y = 468, 499
    inp.x, inp.y, inp.w = 62, 494, 480
    drive_btn.x, drive_btn.y = 556, 494
    reset_btn.x, reset_btn.y = 686, 494
    next_btn.x, next_btn.y = 796, 494
    if S["f"] is not None:
        S["ys"] = [None if (v := safe_eval(S["f"], to_x(px))) is None else OY - v * SCALE for px in range(W)]
    in_game = Page.Current() == "GameFJ"
    for widget in (top, bottom, title, readout, menu_btn, msg, ylab, inp, drive_btn, reset_btn, next_btn):
        widget.visible = in_game


def update_camera():
    """Pan the graph by dragging; wheel/pinch zoom is not in Strife's current Input API."""
    global OX, OY
    mx, my = Input.mouse_x(), Input.mouse_y()
    down = Input.mouse_down()
    just_pressed = down and not S["mouse_down"]
    S["mouse_down"] = down
    on_graph = 0 <= mx <= W and GTOP <= my <= GBOT
    if just_pressed and on_graph:
        S["pan"] = (mx, my, OX, OY)
    if S["pan"]:
        if down:
            sx, sy, start_x, start_y = S["pan"]
            OX, OY = start_x + mx - sx, start_y + my - sy
        else:
            S["pan"] = None


# ---------- game logic ----------
def start_level(i):
    S["level"] = i
    lv = LEVELS[i]
    S["f"], S["err"], S["text"], S["ys"], S["mode"], S["crash"] = None, "", "", [], "edit", None
    S["cx"], S["cy"] = lv["start"]
    inp.text = ""
    title.text = lv["name"]
    readout.text = ""
    next_btn.visible = False
    set_msg(lv["hint"])
    Page.Open("GameFJ")


def rebuild_curve():
    """Re-parse what the player typed and cache the road's screen height for every pixel column."""
    S["mode"], S["crash"] = "edit", None
    S["cx"], S["cy"] = LEVELS[S["level"]]["start"]
    next_btn.visible = False
    S["f"], S["err"], S["ys"] = None, "", []
    if inp.text.strip() == "":
        set_msg(LEVELS[S["level"]]["hint"])
        return
    try:
        S["f"] = parse(inp.text)
    except ValueError as e:
        S["err"] = str(e)
        set_msg(S["err"], "bad")
        return
    ys = []
    for px in range(W):
        v = safe_eval(S["f"], to_x(px))
        ys.append(None if v is None else OY - v * SCALE)
    S["ys"] = ys
    set_msg("Looks good? Press Enter or Drive!")


def hits_wall(x, y):
    m = 0.12  # car half-size, in graph units
    for (x1, y1, x2, y2) in LEVELS[S["level"]]["walls"]:
        if x1 - m < x < x2 + m and y1 - m < y < y2 + m:
            return True
    return False


def drive():
    if S["f"] is None:
        set_msg(S["err"] or "Type a function first.", "bad")
        return
    lv = LEVELS[S["level"]]
    sx, sy = lv["start"]
    y0 = safe_eval(S["f"], sx)
    if y0 is None or abs(y0 - sy) > START_TOL:
        shown = "undefined" if y0 is None else "%.2f" % y0
        set_msg("Your road must start at the car: at x=%g it should be y=%g, but yours is %s." % (sx, sy, shown), "bad")
        return
    S["mode"], S["cx"], S["cy"], S["crash"] = "driving", sx, sy, None
    set_msg("Driving...")


def crash(x, y, why):
    S["mode"], S["crash"] = "crashed", (x, y)
    set_msg("%s  Edit your function and try again." % why, "bad")


def win():
    S["mode"] = "won"
    last = S["level"] == len(LEVELS) - 1
    set_msg("Checkpoint reached!" + (" You finished the whole trip!" if last else ""), "good")
    next_btn.visible = not last
    done = Storage.Load("levels_done", [])
    if S["level"] not in done:
        Storage.Save("levels_done", done + [S["level"]])


drive_btn.on_click = drive
inp.on_submit = lambda text: drive()
reset_btn.on_click = lambda: (setattr(inp, "text", ""), rebuild_curve())
next_btn.on_click = lambda: start_level(min(S["level"] + 1, len(LEVELS) - 1))
menu_btn.on_click = lambda: Page.Open("Menu")
layout_window()


def on_update(dt):
    layout_window()
    if Page.Current() != "GameFJ":
        return
    update_camera()
    if S["f"] is not None:
        S["ys"] = [None if (v := safe_eval(S["f"], to_x(px))) is None else OY - v * SCALE for px in range(W)]
    if inp.text != S["text"]:               # live preview while typing, like Desmos
        S["text"] = inp.text
        rebuild_curve()
    if S["mode"] == "driving":
        lv = LEVELS[S["level"]]
        gx, gy = lv["goal"]
        remaining = SPEED * dt
        while remaining > 0 and S["mode"] == "driving":   # small sub-steps so thin walls can't be skipped
            step = min(0.02, remaining)
            remaining -= step
            x = S["cx"] + step
            y = safe_eval(S["f"], x)
            if y is None:
                crash(S["cx"], S["cy"], "The road has a gap at x=%.1f." % x)
            elif y < -1.5 or y > 7:
                crash(x, max(-1.5, min(7, y)), "The car left the map.")
            elif hits_wall(x, y):
                crash(x, y, "Crashed into an obstacle at x=%.1f." % x)
            else:
                S["cx"], S["cy"] = x, y
                if x >= gx:
                    if abs(y - gy) <= TOL:
                        win()
                    else:
                        crash(x, y, "Missed the flag: at x=%g your road is at y=%.2f, the flag is at y=%g." % (gx, y, gy))
    readout.text = "x = %.2f   y = %.2f" % (S["cx"], S["cy"]) if S["f"] else ""


# ---------- drawing ----------
def box(x, y, w, h, c):
    """Draw.rect clipped to the graph area."""
    x0, y0, x1, y1 = max(x, 0), max(y, GTOP), min(x + w, W), min(y + h, GBOT)
    if x1 > x0 and y1 > y0:
        Draw.rect(x0, y0, x1 - x0, y1 - y0, c)


def draw_car(px, py):
    # wheels sit on the road; body above them
    box(px - 17, py - 16, 34, 11, "#e8590c")
    box(px - 9, py - 24, 20, 9, "#ffa94d")
    box(px - 6, py - 22, 7, 5, "#d0ebff")
    box(px + 2, py - 22, 7, 5, "#d0ebff")
    box(px - 14, py - 8, 9, 9, "#212529")
    box(px + 6, py - 8, 9, 9, "#212529")


def on_draw():
    if Page.Current() == "Menu":
        return
    elif Page.Current() == "GameFJ":
        lv = LEVELS[S["level"]]
        box(0, GTOP, W, GBOT - GTOP, "#fbfcfe")
        min_x, max_x = math.floor(to_x(0)) - 1, math.ceil(to_x(W)) + 1
        min_y = math.floor((OY - GBOT) / SCALE) - 1
        max_y = math.ceil((OY - GTOP) / SCALE) + 1
        for gx in range(min_x, max_x + 1):                      # infinite grid, clipped to the viewport
            px, _ = to_px(gx, 0)
            box(px, GTOP, 1, GBOT - GTOP, "#dde3ea")
        for gy in range(min_y, max_y + 1):
            _, py = to_px(0, gy)
            box(0, py, W, 1, "#dde3ea")
        box(OX - 1, GTOP, 2, GBOT - GTOP, "#495057")           # axes
        box(0, OY - 1, W, 2, "#495057")
        label_y = min(max(OY + 5, GTOP + 3), GBOT - 18)
        label_x = min(max(OX - 22, 3), W - 25)
        label_every = 1 if SCALE >= 38 else 2
        for gx in range(min_x, max_x + 1):
            if gx == 0 or gx % label_every:
                continue
            px, py = to_px(gx, 0)
            Draw.text(str(gx), px - 4, label_y, 14, "#6c757d")
        for gy in range(min_y, max_y + 1):
            if gy == 0 or gy % label_every:
                continue
            px, py = to_px(0, gy)
            Draw.text(str(gy), label_x, py - 8, 14, "#6c757d")

        for (x1, y1, x2, y2) in lv["walls"]:                   # obstacles
            ax, ay = to_px(x1, y2)
            bx, by = to_px(x2, y1)
            box(ax, ay, bx - ax, by - ay, "#c92a2a")
            box(ax, ay, bx - ax, 3, "#e03131")

        ys, sx, gx_ = S["ys"], lv["start"][0], lv["goal"][0]   # the road (bold between start and flag)
        for px in range(W - 1):
            a, b = ys[px] if px < len(ys) else None, ys[px + 1] if px + 1 < len(ys) else None
            if a is None or b is None:
                continue
            inside = sx <= to_x(px) <= gx_
            top_y = min(a, b)
            box(px, int(top_y) - 1, 2, int(abs(a - b)) + 3, "#1971c2" if inside else "#a5c8f0")

        fx, fy = to_px(*lv["goal"])                            # checkpoint flag
        box(fx - 1, fy - 42, 3, 42, "#212529")
        box(fx + 2, fy - 42, 22, 14, "#2f9e44")
        box(fx - 4, fy - 4, 9, 9, "#2f9e44")
        sx_, sy_ = to_px(*lv["start"])                         # start marker
        box(sx_ - 4, sy_ - 4, 9, 9, "#f08c00")

        if S["mode"] == "crashed" and S["crash"]:
            cx, cy = to_px(*S["crash"])
            Draw.text("X", cx - 9, cy - 22, 34, "#c92a2a")
        else:
            cx, cy = to_px(S["cx"], S["cy"])
            draw_car(cx, cy)
