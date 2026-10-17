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
SPEED, EPS = 4.0, 0.02
MARKER_RADIUS = .25
Y_MIN, Y_MAX = -1.5, 7.0


def to_px(x, y): return OX + x * SCALE, OY - y * SCALE
def to_x(px): return (px - OX) / SCALE


S = dict(level=0, f=None, text="", err="", mode="edit", cx=0.0, cy=0.0,
         crash=None, ys=[], road_ys=[], msg="", kind="info", pan=None, endless=False,
         row_count=1, active=[], history=[], start=(0, 0), drive_end=0, missed_checkpoint=False)
E = dict(fuel=100, checkpoints=0, goal=(8, 2), start=(0, 0), active=[], history=[],
         row_count=1, game_over=False, drive_end=0, missed_checkpoint=False, drive_rewards=0)


def set_msg(text, kind="info"):
    S["msg"], S["kind"] = text, kind
    msg.text = text
    msg.color = {"info": "#cfd8e3", "bad": "#ff8a8a", "good": "#8af08a"}[kind]


# ---------- Game page ----------
Page.Open("GameFJ")
top = UI.Frame(0, 0, W, GTOP); top.bg = "dark"
title = UI.Text("", 16, 11, 26); title.color = "white"
readout = UI.Text("", 520, 16, 20); readout.color = "#ffd25a"
fuel_readout = UI.Text("", 380, 16, 20); fuel_readout.color = "#8af08a"
projects_btn = UI.Button("Projects", 580, 8, 120, 34)
fullscreen_btn = UI.Button("Fullscreen", 710, 8, 120, 34)
menu_btn = UI.Button("Menu", 840, 8, 110, 34)
bottom = UI.Frame(0, GBOT, W, H - GBOT); bottom.bg = "panel"
msg = UI.Text("", 16, 468, 18)
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


# ---------- Mode and level menus ----------
Page.Open("Menu")
mode_title = UI.Text("Road Trip", 0, 35, 64); mode_title.color = "#ffd25a"
mode_hint = UI.Text("Choose a game mode", 0, 115, 26); mode_hint.color = "white"
fj_mode_btn = UI.Button("Function Junction", 0, 185, 460, 60)
fj_mode_btn.bg, fj_mode_btn.color = "#1971c2", "white"
fj_mode_btn.on_click = lambda: Page.Open("FunctionJunctionMenu")
bd_mode_btn = UI.Button("Bomb Defusal", 0, 260, 460, 60)
bd_mode_btn.bg, bd_mode_btn.color = "#c92a2a", "white"
mode_endless_btn = UI.Button("Endless Road", 0, 335, 460, 60)
mode_endless_btn.bg, mode_endless_btn.color = "#2f9e44", "white"
mode_endless_btn.on_click = lambda: start_endless()
back_b = UI.Button("Back to Strife Menu", 20, 20, 230, 42); back_b.on_click = Projects.Home


def start_bomb():
    Page.Open("GameBD")
    restart = UI.Get("BombRestart")
    if restart is not None and callable(restart.on_click): restart.on_click()


bd_mode_btn.on_click = start_bomb
Page.Open("FunctionJunctionMenu")
level_title = UI.Text("Function Junction", 0, 25, 42); level_title.color = "#ffd25a"
level_hint = UI.Text("Write y = f(x) to guide the car to the flag.", 0, 80, 20)
level_hint.color = "#cfd8e3"
level_buttons = []
for i, lv in enumerate(LEVELS):
    button = UI.Button(lv["name"] + "  -  " + lv["concept"], 0, 0, 520, 40)
    button.bg, button.color = "#1971c2", "white"
    button.on_click = (lambda n: lambda: start_level(n))(i)
    level_buttons.append(button)
endless_b = UI.Button("Endless Road", 0, 0, 250, 42)
endless_b.bg, endless_b.color = "#2f9e44", "white"
fj_back_btn = UI.Button("Back to modes", 20, 20, 160, 40)
fj_back_btn.bg, fj_back_btn.color = "#495057", "white"
fj_back_btn.on_click = lambda: Page.Open("Menu")
Page.Open("Menu")


def layout_menus():
    mode_title.x, mode_hint.x = W / 2 - 180, W / 2 - 145
    for button in (fj_mode_btn, bd_mode_btn, mode_endless_btn): button.x = W / 2 - 230
    level_title.x, level_hint.x = W / 2 - 210, W / 2 - 230
    columns = 2 if H < 760 else 1
    rows = math.ceil(len(level_buttons) / columns)
    column_width = min(560, (W - 40) / columns)
    button_height = max(26, min(44, (H - 205) / rows - 8))
    for i, button in enumerate(level_buttons):
        column, row = divmod(i, rows)
        button.x = W / 2 - columns * column_width / 2 + column * column_width + 8
        button.y, button.w, button.h = 120 + row * (button_height + 8), column_width - 16, button_height
    endless_b.x, endless_b.y = W / 2 - 125, H - 62


def all_game_widgets():
    return [top, bottom, title, readout, fuel_readout, projects_btn, fullscreen_btn, menu_btn, msg,
            drive_btn, reset_btn, next_btn, endless_hint, restart_btn, result_menu_btn] + [w for r in end_rows for w in r]


def layout_window():
    global W, H, GTOP, GBOT, OX, OY, SCALE, CAMERA_READY
    W, H = Window.width(), Window.height()
    layout_menus()
    GTOP = max(50, round(H * .09))
    if S["endless"]:
        panel_height = 150 if E["game_over"] else 58 + E["row_count"] * 34
    else:
        panel_height = 58 + S["row_count"] * 34
    GBOT = H - panel_height
    if not CAMERA_READY:
        OX, OY, SCALE, CAMERA_READY = max(60, round(W * .065)), GBOT - 40, 60, True
    top.w = bottom.w = W; bottom.y, bottom.h = GBOT, H - GBOT
    readout.x, fuel_readout.x = max(250, W - 430), max(170, W - 570)
    projects_btn.x, fullscreen_btn.x, menu_btn.x = W - 390, W - 260, W - 130
    in_game, normal = Page.Current() == "GameFJ", not S["endless"]
    for w in all_game_widgets(): w.visible = False
    for w in (top, bottom, title, readout, fuel_readout, projects_btn, fullscreen_btn, menu_btn, msg): w.visible = in_game
    if in_game:
        msg.y = GBOT + 8
        if S["endless"] and E["game_over"]:
            restart_btn.x, restart_btn.y = W / 2 - 160, GBOT + 90
            result_menu_btn.x, result_menu_btn.y = W / 2 + 20, GBOT + 90
            restart_btn.visible = result_menu_btn.visible = True
        else:
            row_count = E["row_count"] if S["endless"] else S["row_count"]
            if S["endless"]: endless_hint.x, endless_hint.y, endless_hint.visible = 16, GBOT + 28, True
            row_y = GBOT + 50
            for i, (label, formula, domain, range_) in enumerate(end_rows):
                show = i < row_count
                label.text, label.x, label.y = "f%d(x) =" % (i + 1), 16, row_y + i * 34 + 5
                formula.x, formula.y, formula.w, formula.h = 78, row_y + i * 34, max(160, W - 550), 30
                domain.x, domain.y, domain.w, domain.h = W - 460, row_y + i * 34, 210, 30
                range_.x, range_.y, range_.w, range_.h = W - 240, row_y + i * 34, 210, 30
                for w in (label, formula, domain, range_): w.visible = show
            drive_btn.x, drive_btn.y, reset_btn.x, reset_btn.y = W - 160, GBOT + 7, W - 290, GBOT + 7
            drive_btn.visible = reset_btn.visible = S["mode"] not in ("driving", "won")
            next_btn.x, next_btn.y = W - 450, GBOT + 7
            next_btn.visible = normal and S["mode"] == "won" and S["level"] < len(LEVELS) - 1


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


def marker_connection(f, domain, range_, car_x, car_y, requested_end):
    """Find the first forward point where a road touches the half-grid car marker."""
    start = max(car_x, domain["lo"] if domain["lo"] is not None else car_x)
    stop = min(car_x + MARKER_RADIUS, requested_end)
    if start > stop + EPS: return None
    steps = max(1, int(math.ceil((stop - start) / .005)))
    for number in range(steps + 1):
        x = start + (stop - start) * number / steps
        y = safe_eval(f, x)
        if y is not None and inside(x, domain) and inside(y, range_) and abs(y - car_y) <= MARKER_RADIUS + EPS:
            return x, y
    return None


def touches_marker(x, y, point):
    return abs(x - point[0]) <= MARKER_RADIUS + EPS and abs(y - point[1]) <= MARKER_RADIUS + EPS


def build_route(start, goal_x, row_count):
    x, y, segments, total = start[0], start[1], [], 0
    for i, (_, formula, domain_text, range_text) in enumerate(end_rows[:row_count]):
        if not formula.text.strip(): raise ValueError("Function %d needs a formula" % (i + 1))
        domain, range_ = parse_constraint(domain_text.text, "x"), parse_constraint(range_text.text, "y")
        if domain["hi"] is None and i != row_count - 1: raise ValueError("An unbounded domain must be the last function")
        f = parse(formula.text); requested_end = goal_x if domain["hi"] is None else domain["hi"]
        connection = marker_connection(f, domain, range_, x, y, requested_end)
        if connection is None: raise ValueError("Function %d must touch the car marker" % (i + 1))
        segment_start, _ = connection
        if requested_end <= segment_start + EPS: raise ValueError("Function %d must extend to the right of the car" % (i + 1))
        end = range_limited_end(f, segment_start, requested_end, range_); ey = safe_eval(f, end)
        if end <= segment_start + EPS: raise ValueError("Function %d's range ends at the car" % (i + 1))
        segments.append(dict(f=f, domain=domain, range=range_, start=segment_start, end=end)); total += row_cost(domain); x, y = end, ey
    return segments, total, (x, y)


def build_endless_route(): return build_route(E["start"], E["goal"][0], E["row_count"])


def build_normal_route():
    level = LEVELS[S["level"]]
    return build_route(S["start"], level["goal"][0], 1)


def endless_value_at(x, segments=None):
    for segment in S["active"] if segments is None else segments:
        start, end = segment.get("start", float("-inf")), segment.get("end", float("inf"))
        if start - EPS <= x <= end + EPS and inside(x, segment["domain"]):
            y = safe_eval(segment["f"], x)
            return y if y is not None and inside(y, segment["range"]) else None
    return None


def preview_segments(row_count):
    """Parse whatever is currently typed so the graph previews before Drive."""
    segments = []
    for _, formula, domain_text, range_text in end_rows[:row_count]:
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
        current = S["active"] if S["mode"] == "driving" else preview_segments(E["row_count"])
        segments = E["history"] + current
    else:
        current = S["active"] if S["mode"] in ("driving", "won") else preview_segments(1)
        segments = S["history"] + current
    S["road_ys"] = [[None if (v := endless_value_at(to_x(px), [segment])) is None else OY - v * SCALE
                     for px in range(max(0, W))] for segment in segments]
    S["ys"] = []


def clear_endless_rows():
    E["row_count"] = 1
    for _, formula, domain, range_ in end_rows: formula.text, domain.text, range_.text = "", "{xeR}", "{yeR}"


def clear_normal_rows():
    S["row_count"] = 1
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
    set_msg("Checkpoint 1: reach x=%g, y=%g." % E["goal"]); Page.Open("GameFJ")


# ---------- Normal levels ----------
def start_level(i):
    level_start = LEVELS[i]["start"]
    S.update(endless=False, level=i, f=None, text="", err="", ys=[], road_ys=[], mode="edit", crash=None,
             active=[], history=[], start=level_start, drive_end=level_start[0], missed_checkpoint=False)
    S["cx"], S["cy"] = level_start
    clear_normal_rows(); title.text, readout.text, fuel_readout.text = LEVELS[i]["name"], "", ""
    set_msg(LEVELS[i]["hint"]); Page.Open("GameFJ")


def hits_wall(x, y):
    return any(x1 - .25 < x < x2 + .25 and y1 - .25 < y < y2 + .25 for x1, y1, x2, y2 in LEVELS[S["level"]]["walls"])


def drive_endless():
    if E["game_over"]: return
    try: segments, cost, endpoint = build_endless_route()
    except ValueError as e: set_msg(str(e), "bad"); return
    if cost > E["fuel"] + EPS:
        E["game_over"] = True; set_msg("Out of fuel after %d checkpoint%s." % (E["checkpoints"], "" if E["checkpoints"] == 1 else "s"), "bad"); return
    E["fuel"] -= cost; fuel_readout.text = "Fuel: %.0f" % E["fuel"]
    E["active"], E["drive_end"], E["missed_checkpoint"], E["drive_rewards"] = segments, endpoint[0], False, 0
    S["active"], S["mode"], S["crash"] = segments, "driving", None
    S["cx"] = segments[0]["start"]; S["cy"] = endless_value_at(S["cx"], segments)
    set_msg("Driving to x=%g... %.0f fuel spent." % (endpoint[0], cost))


def drive():
    if S["endless"]: drive_endless(); return
    try: segments, _, endpoint = build_normal_route()
    except ValueError as e: set_msg(str(e), "bad"); return
    S["active"], S["mode"], S["crash"] = segments, "driving", None
    S["drive_end"], S["missed_checkpoint"] = endpoint[0], False
    S["cx"] = segments[0]["start"]; S["cy"] = endless_value_at(S["cx"], segments)
    set_msg("Driving to x=%g..." % endpoint[0])


def crash(x, y, why): S["mode"], S["crash"] = "crashed", (x, y); set_msg(why + " Edit your function and try again.", "bad")
def normal_win():
    S["mode"] = "won"; set_msg("Checkpoint reached!", "good")
    done = Storage.Load("levels_done", [])
    if S["level"] not in done: Storage.Save("levels_done", done + [S["level"]])


def finish_normal_route():
    S["history"].extend(S["active"]); S["active"] = []
    S["start"] = (S["cx"], S["cy"])
    clear_normal_rows()
    if S["missed_checkpoint"]:
        S["mode"], S["crash"] = "crashed", (S["cx"], S["cy"])
        set_msg("The checkpoint is behind the car. Reset the level and try again.", "bad")
    else:
        S["mode"], S["crash"] = "edit", None
        set_msg("Road ended at x=%g, y=%g. Build the next road from here." % (S["cx"], S["cy"]), "good")


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
    else:
        level_start = LEVELS[S["level"]]["start"]
        S["active"], S["history"], S["mode"], S["crash"], S["start"] = [], [], "edit", None, level_start
        S["cx"], S["cy"] = level_start
        clear_normal_rows(); set_msg(LEVELS[S["level"]]["hint"])


drive_btn.on_click = drive; reset_btn.on_click = reset_current
for _, formula_input, _, _ in end_rows: formula_input.on_submit = lambda text: drive()
next_btn.on_click = lambda: start_level(min(S["level"] + 1, len(LEVELS) - 1))
menu_btn.on_click = lambda: Page.Open("Menu"); fullscreen_btn.on_click = Window.toggle_fullscreen; projects_btn.on_click = Projects.Home
endless_b.on_click = start_endless
restart_btn.on_click = start_endless; result_menu_btn.on_click = lambda: Page.Open("Menu")
layout_window()


def on_update(dt):
    layout_window()
    if Page.Current() != "GameFJ": return
    update_camera(); refresh_curve()
    if S["mode"] != "driving": return
    remaining = SPEED * dt
    while remaining > 0 and S["mode"] == "driving":
        step = min(.02, remaining); remaining -= step
        drive_end = E["drive_end"] if S["endless"] else S["drive_end"]
        x = min(S["cx"] + step, drive_end)
        y = endless_value_at(x, S["active"])
        if y is None: crash(S["cx"], S["cy"], "The road has a gap at x=%.1f." % x); continue
        if S["endless"] and (y < Y_MIN or y > Y_MAX):
            crash(x, max(Y_MIN, min(Y_MAX, y)), "The car left the map."); continue
        if not S["endless"] and hits_wall(x, y): crash(x, y, "Crashed into an obstacle at x=%.1f." % x); continue
        S["cx"], S["cy"] = x, y
        if S["endless"]:
            goal = E["goal"]
            if not E["missed_checkpoint"] and touches_marker(x, y, goal): reach_endless_checkpoint()
            elif not E["missed_checkpoint"] and x > goal[0] + MARKER_RADIUS: E["missed_checkpoint"] = True
            if x >= E["drive_end"] and S["mode"] == "driving":
                finish_endless_route()
        else:
            goal = LEVELS[S["level"]]["goal"]
            if not S["missed_checkpoint"] and touches_marker(x, y, goal):
                S["history"].extend(S["active"]); S["active"] = []; normal_win()
            elif not S["missed_checkpoint"] and x > goal[0] + MARKER_RADIUS: S["missed_checkpoint"] = True
            if x >= S["drive_end"] and S["mode"] == "driving": finish_normal_route()
    readout.text = "x = %.2f   y = %.2f" % (S["cx"], S["cy"])


# ---------- Drawing ----------
def box(x, y, w, h, c):
    x0, y0, x1, y1 = max(x, 0), max(y, GTOP), min(x + w, W), min(y + h, GBOT)
    if x1 > x0 and y1 > y0: Draw.rect(x0, y0, x1 - x0, y1 - y0, c)


def draw_car(px, py):
    diameter = SCALE * .5
    body_h, cabin_w, cabin_h, wheel = diameter * .34, diameter * .56, diameter * .28, diameter * .22
    box(px - diameter / 2, py - body_h, diameter, body_h, "#e8590c")
    box(px - cabin_w / 2, py - body_h - cabin_h, cabin_w, cabin_h, "#ffa94d")
    box(px - cabin_w * .34, py - body_h - cabin_h * .82, cabin_w * .28, cabin_h * .55, "#d0ebff")
    box(px + cabin_w * .06, py - body_h - cabin_h * .82, cabin_w * .28, cabin_h * .55, "#d0ebff")
    box(px - diameter * .36, py - wheel * .65, wheel, wheel, "#212529")
    box(px + diameter * .14, py - wheel * .65, wheel, wheel, "#212529")


def on_draw():
    if Page.Current() != "GameFJ": return
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
        start, goal = S["start"], LEVELS[S["level"]]["goal"]
    for road in S["road_ys"]:
        for px in range(W - 1):
            a = road[px] if px < len(road) else None; b = road[px + 1] if px + 1 < len(road) else None
            if a is not None and b is not None: box(px, int(min(a, b)) - 1, 2, int(abs(a - b)) + 3, "#1971c2")
    marker = SCALE * .5; pole_h, pole_w = marker * 1.5, max(2, marker * .08)
    fx, fy = to_px(*goal)
    box(fx - pole_w / 2, fy - pole_h, pole_w, pole_h, "#212529")
    box(fx + pole_w / 2, fy - pole_h, marker * .75, marker * .35, "#2f9e44")
    box(fx - marker / 2, fy - marker / 2, marker, marker, "#2f9e44")
    sx, sy = to_px(*start); box(sx - marker / 2, sy - marker / 2, marker, marker, "#f08c00")
    if S["mode"] == "crashed" and S["crash"]:
        cx, cy = to_px(*S["crash"]); Draw.text("X", cx - 9, cy - 22, 34, "#c92a2a")
    else:
        cx, cy = to_px(S["cx"], S["cy"]); draw_car(cx, cy)
