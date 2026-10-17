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
CAMERA_READY = False
SPEED = 4.0                     # car speed, graph units per second
TOL = 0.35                      # how close to the flag counts as reaching it
START_TOL = 0.3                 # how close the road must pass to the car's start


def to_px(x, y):
    return OX + x * SCALE, OY - y * SCALE


def to_x(px):
    return (px - OX) / SCALE


# ---------- game state ----------
S = dict(level=0, f=None, text="", err="", mode="edit", cx=0.0, cy=0.0, crash=None, ys=[], msg="", kind="info", pan=None)


def set_msg(text, kind="info"):
    S["msg"], S["kind"] = text, kind
    msg.text = text
    msg.color = {"info": "#cfd8e3", "bad": "#ff8a8a", "good": "#8af08a"}[kind]


# ---------- Game page ----------
Page.Open("Game")
top = UI.Frame(0, 0, W, GTOP)
top.bg = "dark"
title = UI.Text("", 16, 11, 26)
title.color = "white"
readout = UI.Text("", 520, 16, 20)
readout.color = "#ffd25a"
menu_btn = UI.Button("Menu", 840, 8, 110, 34)
fullscreen_btn = UI.Button("Fullscreen", 710, 8, 120, 34)

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


# ---------- Menu page ----------
Page.Open("Menu")
UI.Text("Road Trip", 300, 50, 72).color = "#ffd25a"
UI.Text("Function Junction", 330, 130, 36).color = "white"
UI.Text("Drive the car to the flag by writing the road as a function, y = f(x).", 190, 190, 20).color = "#cfd8e3"
for i, lv in enumerate(LEVELS):
    b = UI.Button(lv["name"] + "  -  " + lv["concept"], 250, 250 + i * 62, 460, 50)
    b.bg = "#1971c2"
    b.color = "white"
    b.on_click = (lambda n: lambda: start_level(n))(i)

def layout_window():
    global W, H, GTOP, GBOT, OY, OX, SCALE, CAMERA_READY
    W, H = Window.width(), Window.height()
    GTOP = max(50, round(H * 0.09))
    GBOT = H - max(80, round(H * 0.15))
    if not CAMERA_READY:
        OX, OY = max(60, round(W * 0.065)), GBOT - max(40, round(H * 0.075))
        SCALE = max(24, min(60, (W - OX - 40) / 14))
        CAMERA_READY = True
    top.w = bottom.w = W
    readout.x = max(250, W - 430)
    fullscreen_btn.x, menu_btn.x = W - 260, W - 130
    bottom.y, bottom.h = GBOT, H - GBOT
    msg.y, ylab.y = GBOT + 8, H - 43
    inp.y = drive_btn.y = reset_btn.y = next_btn.y = H - 46
    inp.w = max(140, W - 490)
    drive_btn.x, reset_btn.x, next_btn.x = W - 390, W - 260, W - 150
    if S["f"] is not None:
        S["ys"] = [None if (v := safe_eval(S["f"], to_x(px))) is None else OY - v * SCALE for px in range(W)]
    in_game = Page.Current() == "Game"
    for widget in (top, bottom, title, readout, menu_btn, fullscreen_btn, msg, ylab, inp, drive_btn, reset_btn, next_btn):
        widget.visible = in_game


def update_camera():
    """Pan the graph by dragging and zoom around the pointer."""
    global OX, OY, SCALE
    mx, my = Input.mouse_x(), Input.mouse_y()
    on_graph = 0 <= mx <= W and GTOP <= my <= GBOT
    if Input.mouse_pressed() and on_graph:
        S["pan"] = (mx, my, OX, OY)
    if S["pan"]:
        if Input.mouse_down():
            sx, sy, start_x, start_y = S["pan"]
            OX, OY = start_x + mx - sx, start_y + my - sy
        else:
            S["pan"] = None
    zoom = Input.mouse_wheel() + Input.pinch()
    if on_graph and zoom:
        world_x, world_y = to_x(mx), (OY - my) / SCALE
        SCALE = max(24, min(220, SCALE * (1.15 ** zoom)))
        OX, OY = mx - world_x * SCALE, my + world_y * SCALE


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
    Page.Open("Game")


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
fullscreen_btn.on_click = Window.toggle_fullscreen
layout_window()


def on_update(dt):
    layout_window()
    if Page.Current() != "Game":
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
    if Page.Current() != "Game":
        return
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
