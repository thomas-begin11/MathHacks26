# Road Trip: Function Junction - a Strife! project (Python)
import math
import random
import re
import sys

for _m in ("mathparse", "levels"):
    sys.modules.pop(_m, None)
from mathparse import parse, safe_eval
from levels import LEVELS

W, H = 960, 540
GTOP, GBOT = 50, 460
SCALE, OX, OY = 60, 60, 420
CAMERA_READY = False
SPEED, TOL, START_TOL, CONNECT_TOL, EPS = 4.0, 0.35, 0.3, 0.05, 0.02
Y_MIN, Y_MAX = -1.5, 7.0


def to_px(x, y): return OX + x * SCALE, OY - y * SCALE
def to_x(px): return (px - OX) / SCALE


S = dict(level=0, f=None, text="", err="", mode="edit", cx=0.0, cy=0.0,
         crash=None, ys=[], road_ys=[], msg="", kind="info", pan=None, endless=False)
E = dict(fuel=100, checkpoints=0, goal=(8, 2), start=(0, 0), active=[], history=[],
         row_count=1, game_over=False, drive_end=0, missed_checkpoint=False, drive_rewards=0)


def set_msg(text, kind="info"):
    S["msg"], S["kind"] = text, kind
    msg.text = text
    msg.color = {"info": "#cfd8e3", "bad": "#ff8a8a", "good": "#8af08a"}[kind]


# ---------- Game page ----------
Page.Open("Game")
top = UI.Frame(0, 0, W, GTOP); top.bg = "dark"
title = UI.Text("", 16, 11, 26); title.color = "white"
readout = UI.Text("", 520, 16, 20); readout.color = "#ffd25a"
fuel_readout = UI.Text("", 380, 16, 20); fuel_readout.color = "#8af08a"
projects_btn = UI.Button("Projects", 580, 8, 120, 34)
fullscreen_btn = UI.Button("Fullscreen", 710, 8, 120, 34)
menu_btn = UI.Button("Menu", 840, 8, 110, 34)
bottom = UI.Frame(0, GBOT, W, H - GBOT); bottom.bg = "panel"
msg = UI.Text("", 16, 468, 18)
ylab = UI.Text("y =", 16, 499, 26); ylab.color = "white"
inp = UI.Input("type a function, e.g. 0.3x + 1", 62, 494, 480, 38)
drive_btn = UI.Button("Drive!", 556, 494, 120, 38)
reset_btn = UI.Button("Reset", 686, 494, 100, 38)
next_btn = UI.Button("Next level", 796, 494, 148, 38)
endless_hint = UI.Text("", 16, 0, 16); endless_hint.color = "#cfd8e3"
restart_btn = UI.Button("Restart Endless", 0, 0, 180, 40)
result_menu_btn = UI.Button("Menu", 0, 0, 120, 40)
end_rows = []
for number in range(1):
    label = UI.Text("", 0, 0, 16); label.color = "#cfd8e3"
    formula = UI.Input("formula, e.g. x^2 - 3x + 2", 0, 0, 260, 34)
    domain = UI.Input("{xeR}", 0, 0, 150, 30); domain.text = "{xeR}"
    range_ = UI.Input("{yeR}", 0, 0, 150, 30); range_.text = "{yeR}"
    end_rows.append((label, formula, domain, range_))
Theme.Set("modern")
for _b, _c in ((projects_btn, "#495057"), (fullscreen_btn, "#495057"), (menu_btn, "#495057"),
               (drive_btn, "#2f9e44"), (reset_btn, "#868e96"), (next_btn, "#1971c2"),
               (restart_btn, "#2f9e44"), (result_menu_btn, "#495057")):
    _b.bg, _b.color = _c, "white"


# ---------- Menu page ----------
Page.Open("Menu")
UI.Text("Road Trip", 300, 50, 72).color = "#ffd25a"
UI.Text("Function Junction", 330, 130, 36).color = "white"
UI.Text("Drive the car to the flag by writing the road as a function, y = f(x).", 190, 190, 20).color = "#cfd8e3"
for i, lv in enumerate(LEVELS):
    b = UI.Button(lv["name"] + "  -  " + lv["concept"], 250, 250 + i * 62, 460, 50)
    b.bg, b.color = "#1971c2", "white"
    b.on_click = (lambda n: lambda: start_level(n))(i)
endless_b = UI.Button("Endless", 350, 500, 250, 50); endless_b.bg, endless_b.color = "#1971c2", "white"
back_b = UI.Button("Back to Strife Menu", 20, 20, 250, 50); back_b.on_click = Projects.Home


def all_game_widgets():
    return [top, bottom, title, readout, fuel_readout, projects_btn, fullscreen_btn, menu_btn, msg, ylab,
            inp, drive_btn, reset_btn, next_btn, endless_hint, restart_btn, result_menu_btn] + [w for r in end_rows for w in r]


def layout_window():
    global W, H, GTOP, GBOT, OX, OY, SCALE, CAMERA_READY
    W, H = Window.width(), Window.height()
    GTOP = max(50, round(H * .09))
    if S["endless"]:
        panel_height = 150 if E["game_over"] else 58 + E["row_count"] * 34
    else:
        panel_height = max(80, round(H * .15))
    GBOT = H - panel_height
    if not CAMERA_READY:
        OX, OY, SCALE, CAMERA_READY = max(60, round(W * .065)), GBOT - 40, 60, True
    top.w = bottom.w = W; bottom.y, bottom.h = GBOT, H - GBOT
    readout.x, fuel_readout.x = max(250, W - 430), max(170, W - 570)
    projects_btn.x, fullscreen_btn.x, menu_btn.x = W - 390, W - 260, W - 130
    in_game, normal = Page.Current() == "Game", not S["endless"]
    for w in all_game_widgets(): w.visible = False
    for w in (top, bottom, title, readout, fuel_readout, projects_btn, fullscreen_btn, menu_btn, msg): w.visible = in_game
    if normal and in_game:
        msg.y, ylab.y = GBOT + 8, H - 43
        inp.y = drive_btn.y = reset_btn.y = next_btn.y = H - 46
        inp.w, drive_btn.x, reset_btn.x, next_btn.x = max(140, W - 490), W - 390, W - 260, W - 150
        ylab.visible = inp.visible = drive_btn.visible = reset_btn.visible = True
        next_btn.visible = S["mode"] == "won" and S["level"] < len(LEVELS) - 1
    elif in_game:
        msg.y = GBOT + 8
        if E["game_over"]:
            restart_btn.x, restart_btn.y = W / 2 - 160, GBOT + 90
            result_menu_btn.x, result_menu_btn.y = W / 2 + 20, GBOT + 90
            restart_btn.visible = result_menu_btn.visible = True
        else:
            endless_hint.x, endless_hint.y, endless_hint.visible = 16, GBOT + 28, True
            row_y = GBOT + 50
            for i, (label, formula, domain, range_) in enumerate(end_rows):
                show = i < E["row_count"]
                label.text, label.x, label.y = "f%d(x) =" % (i + 1), 16, row_y + i * 34 + 5
                formula.x, formula.y, formula.w, formula.h = 78, row_y + i * 34, max(160, W - 550), 30
                domain.x, domain.y, domain.w, domain.h = W - 460, row_y + i * 34, 210, 30
                range_.x, range_.y, range_.w, range_.h = W - 240, row_y + i * 34, 210, 30
                for w in (label, formula, domain, range_): w.visible = show
            drive_btn.x, drive_btn.y, reset_btn.x, reset_btn.y = W - 160, GBOT + 7, W - 290, GBOT + 7
            drive_btn.visible = reset_btn.visible = S["mode"] != "driving"


def update_camera():
    global OX, OY, SCALE
    mx, my = Input.mouse_x(), Input.mouse_y(); on_graph = 0 <= mx <= W and GTOP <= my <= GBOT
    if Input.mouse_pressed() and on_graph: S["pan"] = (mx, my, OX, OY)
    if S["pan"]:
        if Input.mouse_down():
            sx, sy, ox, oy = S["pan"]; OX, OY = ox + mx - sx, oy + my - sy
        else: S["pan"] = None
    zoom = Input.mouse_wheel() + Input.pinch()
    if on_graph and zoom:
        x, y = to_x(mx), (OY - my) / SCALE; SCALE = max(24, min(220, SCALE * 1.15 ** zoom)); OX, OY = mx - x * SCALE, my + y * SCALE


# ---------- Endless constraints and routes ----------
def parse_constraint(text, variable):
    raw = (str(text).strip().lower().replace(" ", "").replace("∈", "e")
           .replace("≤", "<=").replace("≥", ">="))
    if raw.startswith("{") and raw.endswith("}"): raw = raw[1:-1]
    if raw in (variable + "er", variable + "inr"): return dict(lo=None, hi=None, kind="all")
    for prefix in (variable + "er|", variable + "inr|"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    num = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"
    match = re.fullmatch(variable + r"=(" + num + ")", raw)
    if match:
        value = float(match.group(1))
        return dict(lo=value, hi=value, kind="equal")
    match = re.fullmatch(variable + r"(<=|>=|<|>)(" + num + ")", raw)
    if match:
        op, value = match.group(1), float(match.group(2))
        return dict(lo=value if op in (">", ">=") else None, hi=value if op in ("<", "<=") else None, kind="one")
    match = re.fullmatch("(" + num + r")(<=|<|>=|>)" + variable + r"(<=|<|>=|>)(" + num + ")", raw)
    if match:
        first, left_op, right_op, second = float(match.group(1)), match.group(2), match.group(3), float(match.group(4))
        if (left_op.startswith("<")) != (right_op.startswith("<")):
            raise ValueError("Both sides of the %s constraint must point the same way" % variable)
        lo, hi = min(first, second), max(first, second)
        if lo == hi: return dict(lo=lo, hi=hi, kind="equal")
        return dict(lo=lo, hi=hi, kind="finite")
    raise ValueError("Use {%seR}, {%seR|%s>4}, {%s=2}, 0<=%s<=10, or 10>=%s>=0" %
                     (variable, variable, variable, variable, variable, variable))


def inside(value, rule, tolerance=EPS):
    return ((rule["lo"] is None or value >= rule["lo"] - tolerance) and
            (rule["hi"] is None or value <= rule["hi"] + tolerance))


def row_cost(domain): return 60 if domain["kind"] == "all" else 40 if domain["kind"] == "one" else 10 + 2 * (domain["hi"] - domain["lo"])


def range_limited_end(f, start, end, range_):
    """Return the first point where a continuous road leaves its allowed range."""
    distance = end - start
    steps = min(5000, max(1, int(math.ceil(distance / .02))))
    previous = start
    for number in range(1, steps + 1):
        current = start + distance * number / steps
        value = safe_eval(f, current)
        if value is None or not inside(value, range_, 1e-7):
            low, high = previous, current
            for _ in range(24):
                middle = (low + high) / 2
                middle_value = safe_eval(f, middle)
                if middle_value is not None and inside(middle_value, range_, 1e-7): low = middle
                else: high = middle
            return low
        previous = current
    return end


def build_endless_route():
    goal_x = E["goal"][0]; x, y, segments, total = E["start"][0], E["start"][1], [], 0
    for i, (_, formula, domain_text, range_text) in enumerate(end_rows[:E["row_count"]]):
        if not formula.text.strip(): raise ValueError("Function %d needs a formula" % (i + 1))
        domain, range_ = parse_constraint(domain_text.text, "x"), parse_constraint(range_text.text, "y")
        if domain["lo"] is not None and abs(domain["lo"] - x) > EPS: raise ValueError("Function %d must start at x=%g" % (i + 1, x))
        if domain["hi"] is None and i != E["row_count"] - 1: raise ValueError("An unbounded domain must be the last function")
        f = parse(formula.text); sy = safe_eval(f, x); requested_end = goal_x if domain["hi"] is None else domain["hi"]
        if requested_end <= x + EPS: raise ValueError("Function %d must extend to the right of x=%g" % (i + 1, x))
        if sy is None or not inside(sy, range_) or abs(sy - y) > CONNECT_TOL:
            shown = "undefined" if sy is None else "%g" % sy
            raise ValueError("Function %d must connect at x=%g: road y=%s, car y=%g" %
                             (i + 1, x, shown, y))
        end = range_limited_end(f, x, requested_end, range_); ey = safe_eval(f, end)
        if end <= x + EPS: raise ValueError("Function %d's range ends at its starting point" % (i + 1))
        segments.append(dict(f=f, domain=domain, range=range_, start=x, end=end)); total += row_cost(domain); x, y = end, ey
    return segments, total, (x, y)


def endless_value_at(x, segments=None):
    for segment in S["active"] if segments is None else segments:
        start, end = segment.get("start", float("-inf")), segment.get("end", float("inf"))
        if start - EPS <= x <= end + EPS and inside(x, segment["domain"]):
            y = safe_eval(segment["f"], x)
            return y if y is not None and inside(y, segment["range"]) else None
    return None


def preview_endless_segments():
    """Parse whatever is currently typed so the graph previews before Drive."""
    segments = []
    for _, formula, domain_text, range_text in end_rows[:E["row_count"]]:
        if not formula.text.strip():
            continue
        try:
            segments.append(dict(f=parse(formula.text),
                                 domain=parse_constraint(domain_text.text, "x"),
                                 range=parse_constraint(range_text.text, "y")))
        except ValueError:
            continue
    return segments


def refresh_curve():
    if S["endless"]:
        current = S["active"] if S["mode"] == "driving" else preview_endless_segments()
        segments = E["history"] + current
        S["road_ys"] = [[None if (v := endless_value_at(to_x(px), [segment])) is None else OY - v * SCALE
                         for px in range(max(0, W))] for segment in segments]
        S["ys"] = []
    elif S["f"] is not None:
        S["road_ys"] = []
        S["ys"] = [None if (v := safe_eval(S["f"], to_x(px))) is None else OY - v * SCALE for px in range(max(0, W))]


def clear_endless_rows():
    E["row_count"] = 1
    for _, formula, domain, range_ in end_rows: formula.text, domain.text, range_.text = "", "{xeR}", "{yeR}"


def generate_checkpoint(base_x=None):
    gap = min(16, 8 + E["checkpoints"])
    if base_x is None: base_x = E["start"][0]
    E["goal"] = (base_x + gap, round(random.uniform(0, 5.5) * 2) / 2)


def start_endless():
    S.update(endless=True, f=None, text="", err="", mode="edit", cx=0.0, cy=0.0, crash=None)
    E.update(fuel=100, checkpoints=0, start=(0, 0), active=[], history=[], game_over=False,
             drive_end=0, missed_checkpoint=False, drive_rewards=0)
    S["active"], S["ys"], S["road_ys"] = [], [], []
    clear_endless_rows(); generate_checkpoint(); title.text, fuel_readout.text = "Endless Road", "Fuel: 100"
    endless_hint.text = "Build roads to the flag. Fuel cost is based on each function's domain."
    set_msg("Checkpoint 1: reach x=%g, y=%g." % E["goal"]); Page.Open("Game")


# ---------- Normal levels ----------
def start_level(i):
    S.update(endless=False, level=i, f=None, text="", err="", ys=[], road_ys=[], mode="edit", crash=None)
    S["cx"], S["cy"] = LEVELS[i]["start"]; inp.text, title.text, readout.text, fuel_readout.text = "", LEVELS[i]["name"], "", ""
    set_msg(LEVELS[i]["hint"]); Page.Open("Game")


def rebuild_curve():
    S["mode"], S["crash"], S["f"], S["err"], S["ys"] = "edit", None, None, "", []
    S["cx"], S["cy"] = LEVELS[S["level"]]["start"]
    if not inp.text.strip(): set_msg(LEVELS[S["level"]]["hint"]); return
    try: S["f"] = parse(inp.text)
    except ValueError as e: S["err"] = str(e); set_msg(S["err"], "bad"); return
    refresh_curve(); set_msg("Looks good? Press Enter or Drive!")


def hits_wall(x, y):
    return any(x1 - .12 < x < x2 + .12 and y1 - .12 < y < y2 + .12 for x1, y1, x2, y2 in LEVELS[S["level"]]["walls"])


def drive_endless():
    if E["game_over"]: return
    try: segments, cost, endpoint = build_endless_route()
    except ValueError as e: set_msg(str(e), "bad"); return
    if cost > E["fuel"] + EPS:
        E["game_over"] = True; set_msg("Out of fuel after %d checkpoint%s." % (E["checkpoints"], "" if E["checkpoints"] == 1 else "s"), "bad"); return
    E["fuel"] -= cost; fuel_readout.text = "Fuel: %.0f" % E["fuel"]
    E["active"], E["drive_end"], E["missed_checkpoint"], E["drive_rewards"] = segments, endpoint[0], False, 0
    S["active"], S["mode"], S["crash"] = segments, "driving", None
    set_msg("Driving to x=%g... %.0f fuel spent." % (endpoint[0], cost))


def drive():
    if S["endless"]: drive_endless(); return
    if S["f"] is None: set_msg(S["err"] or "Type a function first.", "bad"); return
    sx, sy = LEVELS[S["level"]]["start"]; y0 = safe_eval(S["f"], sx)
    if y0 is None or abs(y0 - sy) > START_TOL: set_msg("Your road must start at the car.", "bad"); return
    S["mode"], S["cx"], S["cy"], S["crash"] = "driving", sx, sy, None; set_msg("Driving...")


def crash(x, y, why): S["mode"], S["crash"] = "crashed", (x, y); set_msg(why + " Edit your function and try again.", "bad")
def normal_win():
    S["mode"] = "won"; set_msg("Checkpoint reached!", "good")
    done = Storage.Load("levels_done", [])
    if S["level"] not in done: Storage.Save("levels_done", done + [S["level"]])


def reach_endless_checkpoint():
    old_goal_x = E["goal"][0]
    E["checkpoints"] += 1; E["fuel"] += 30; E["drive_rewards"] += 1
    generate_checkpoint(old_goal_x); fuel_readout.text = "Fuel: %.0f" % E["fuel"]


def finish_endless_route():
    E["history"].extend(S["active"]); E["active"] = []
    S["active"], S["mode"], E["start"] = [], "edit", (S["cx"], S["cy"])
    clear_endless_rows()
    if E["missed_checkpoint"]:
        E["game_over"] = True
        set_msg("The checkpoint is behind the car. Run over after %d checkpoint%s." %
                (E["checkpoints"], "" if E["checkpoints"] == 1 else "s"), "bad")
    elif E["drive_rewards"]:
        set_msg("Checkpoint %d reached! +%d fuel. Road ended at x=%g, y=%g." %
                (E["checkpoints"], 30 * E["drive_rewards"], S["cx"], S["cy"]), "good")
    else:
        set_msg("Road ended at x=%g, y=%g. Build the next road from here." % (S["cx"], S["cy"]), "good")


def reset_current():
    if S["endless"]: S["active"] = []; E["active"] = []; clear_endless_rows(); set_msg("Route cleared.")
    else: inp.text = ""; rebuild_curve()


drive_btn.on_click = drive; inp.on_submit = lambda text: drive(); reset_btn.on_click = reset_current
next_btn.on_click = lambda: start_level(min(S["level"] + 1, len(LEVELS) - 1))
menu_btn.on_click = lambda: Page.Open("Menu"); fullscreen_btn.on_click = Window.toggle_fullscreen; projects_btn.on_click = Projects.Home
endless_b.on_click = start_endless
restart_btn.on_click = start_endless; result_menu_btn.on_click = lambda: Page.Open("Menu")
layout_window()


def on_update(dt):
    layout_window()
    if Page.Current() != "Game": return
    update_camera(); refresh_curve()
    if not S["endless"] and inp.text != S["text"]: S["text"] = inp.text; rebuild_curve()
    if S["mode"] != "driving": return
    remaining = SPEED * dt
    while remaining > 0 and S["mode"] == "driving":
        step = min(.02, remaining); remaining -= step
        x = min(S["cx"] + step, E["drive_end"]) if S["endless"] else S["cx"] + step
        y = endless_value_at(x) if S["endless"] else safe_eval(S["f"], x)
        if y is None: crash(S["cx"], S["cy"], "The road has a gap at x=%.1f." % x); continue
        if y < Y_MIN or y > Y_MAX: crash(x, max(Y_MIN, min(Y_MAX, y)), "The car left the map."); continue
        if not S["endless"] and hits_wall(x, y): crash(x, y, "Crashed into an obstacle at x=%.1f." % x); continue
        S["cx"], S["cy"] = x, y
        if S["endless"]:
            goal = E["goal"]
            if not E["missed_checkpoint"] and x >= goal[0]:
                checkpoint_y = endless_value_at(goal[0])
                if checkpoint_y is not None and abs(checkpoint_y - goal[1]) <= TOL:
                    reach_endless_checkpoint()
                else:
                    E["missed_checkpoint"] = True
            if x >= E["drive_end"] and S["mode"] == "driving":
                finish_endless_route()
        else:
            goal = LEVELS[S["level"]]["goal"]
            if x >= goal[0]:
                if abs(y - goal[1]) <= TOL: normal_win()
                else: crash(x, y, "Missed the flag.")
    readout.text = "x = %.2f   y = %.2f" % (S["cx"], S["cy"])


# ---------- Drawing ----------
def box(x, y, w, h, c):
    x0, y0, x1, y1 = max(x, 0), max(y, GTOP), min(x + w, W), min(y + h, GBOT)
    if x1 > x0 and y1 > y0: Draw.rect(x0, y0, x1 - x0, y1 - y0, c)


def draw_car(px, py):
    box(px - 17, py - 16, 34, 11, "#e8590c"); box(px - 9, py - 24, 20, 9, "#ffa94d")
    box(px - 6, py - 22, 7, 5, "#d0ebff"); box(px + 2, py - 22, 7, 5, "#d0ebff")
    box(px - 14, py - 8, 9, 9, "#212529"); box(px + 6, py - 8, 9, 9, "#212529")


def on_draw():
    if Page.Current() != "Game": return
    box(0, GTOP, W, GBOT - GTOP, "#fbfcfe")
    min_x, max_x = math.floor(to_x(0)) - 1, math.ceil(to_x(W)) + 1
    min_y, max_y = math.floor((OY - GBOT) / SCALE) - 1, math.ceil((OY - GTOP) / SCALE) + 1
    for gx in range(min_x, max_x + 1): px, _ = to_px(gx, 0); box(px, GTOP, 1, GBOT - GTOP, "#dde3ea")
    for gy in range(min_y, max_y + 1): _, py = to_px(0, gy); box(0, py, W, 1, "#dde3ea")
    box(OX - 1, GTOP, 2, GBOT - GTOP, "#495057"); box(0, OY - 1, W, 2, "#495057")
    label_y, label_x, every = min(max(OY + 5, GTOP + 3), GBOT - 18), min(max(OX - 22, 3), W - 25), (1 if SCALE >= 38 else 2)
    for gx in range(min_x, max_x + 1):
        if gx and not gx % every: px, _ = to_px(gx, 0); Draw.text(str(gx), px - 4, label_y, 14, "#6c757d")
    for gy in range(min_y, max_y + 1):
        if gy and not gy % every: _, py = to_px(0, gy); Draw.text(str(gy), label_x, py - 8, 14, "#6c757d")
    if S["endless"]: start, goal = E["start"], E["goal"]
    else:
        for x1, y1, x2, y2 in LEVELS[S["level"]]["walls"]:
            ax, ay = to_px(x1, y2); bx, by = to_px(x2, y1); box(ax, ay, bx - ax, by - ay, "#c92a2a"); box(ax, ay, bx - ax, 3, "#e03131")
        start, goal = LEVELS[S["level"]]["start"], LEVELS[S["level"]]["goal"]
    for road in S["road_ys"] if S["endless"] else [S["ys"]]:
        for px in range(W - 1):
            a = road[px] if px < len(road) else None; b = road[px + 1] if px + 1 < len(road) else None
            if a is not None and b is not None: box(px, int(min(a, b)) - 1, 2, int(abs(a - b)) + 3, "#1971c2")
    fx, fy = to_px(*goal); box(fx - 1, fy - 42, 3, 42, "#212529"); box(fx + 2, fy - 42, 22, 14, "#2f9e44"); box(fx - 4, fy - 4, 9, 9, "#2f9e44")
    sx, sy = to_px(*start); box(sx - 4, sy - 4, 9, 9, "#f08c00")
    if S["mode"] == "crashed" and S["crash"]:
        cx, cy = to_px(*S["crash"]); Draw.text("X", cx - 9, cy - 22, 34, "#c92a2a")
    else:
        cx, cy = to_px(S["cx"], S["cy"]); draw_car(cx, cy)
