"""Game rules and movement: parsing what the player typed, driving the car, crashes and wins.
Talks to the screen only through ui.py's helper functions."""
from mathparse import parse, safe_eval
from levels import LEVELS
from state import S
from config import to_px, to_x, W, OY, SCALE, SPEED, TOL, START_TOL
import ui

Page = Storage = None           # Strife's API; filled in by bind()


def bind(api):
    globals().update(api)


def start_level(i):
    S["level"] = i
    lv = LEVELS[i]
    S["f"], S["err"], S["text"], S["ys"], S["mode"], S["crash"] = None, "", "", [], "edit", None
    S["cx"], S["cy"] = lv["start"]
    ui.clear_input()
    ui.set_title(lv["name"])
    ui.set_readout("")
    ui.show_next(False)
    ui.set_msg(lv["hint"])
    Page.Open("Game")


def rebuild_curve():
    """Re-parse what the player typed and cache the road's screen height for every pixel column."""
    S["mode"], S["crash"] = "edit", None
    S["cx"], S["cy"] = LEVELS[S["level"]]["start"]
    ui.show_next(False)
    S["f"], S["err"], S["ys"] = None, "", []
    if ui.input_text().strip() == "":
        ui.set_msg(LEVELS[S["level"]]["hint"])
        return
    try:
        S["f"] = parse(ui.input_text())
    except ValueError as e:
        S["err"] = str(e)
        ui.set_msg(S["err"], "bad")
        return
    ys = []
    for px in range(W):
        v = safe_eval(S["f"], to_x(px))
        ys.append(None if v is None else OY - v * SCALE)
    S["ys"] = ys
    ui.set_msg("Looks good? Press Enter or Drive!")


def hits_wall(x, y):
    m = 0.12  # car half-size, in graph units
    for (x1, y1, x2, y2) in LEVELS[S["level"]]["walls"]:
        if x1 - m < x < x2 + m and y1 - m < y < y2 + m:
            return True
    return False


def drive():
    if S["f"] is None:
        ui.set_msg(S["err"] or "Type a function first.", "bad")
        return
    lv = LEVELS[S["level"]]
    sx, sy = lv["start"]
    y0 = safe_eval(S["f"], sx)
    if y0 is None or abs(y0 - sy) > START_TOL:
        shown = "undefined" if y0 is None else "%.2f" % y0
        ui.set_msg("Your road must start at the car: at x=%g it should be y=%g, but yours is %s." % (sx, sy, shown), "bad")
        return
    S["mode"], S["cx"], S["cy"], S["crash"] = "driving", sx, sy, None
    ui.set_msg("Driving...")


def crash(x, y, why):
    S["mode"], S["crash"] = "crashed", (x, y)
    ui.set_msg("%s  Edit your function and try again." % why, "bad")


def win():
    S["mode"] = "won"
    last = S["level"] == len(LEVELS) - 1
    ui.set_msg("Checkpoint reached!" + (" You finished the whole trip!" if last else ""), "good")
    ui.show_next(not last)
    done = Storage.Load("levels_done", [])
    if S["level"] not in done:
        Storage.Save("levels_done", done + [S["level"]])


def reset():
    ui.clear_input()
    rebuild_curve()


def next_level():
    start_level(min(S["level"] + 1, len(LEVELS) - 1))


def update(dt):
    """Called every frame while the Game page is showing."""
    if ui.input_text() != S["text"]:            # live preview while typing, like Desmos
        S["text"] = ui.input_text()
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
    ui.set_readout("x = %.2f   y = %.2f" % (S["cx"], S["cy"]) if S["f"] else "")
