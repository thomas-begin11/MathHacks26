"""Everything drawn on the graph each frame: grid, axes, obstacles, the road, the flag and the car.
Strife's Draw.* calls only work inside on_draw, so main.py calls scene() from there."""
from levels import LEVELS
from state import S
from config import W, GTOP, GBOT, OX, OY, to_px, to_x

Draw = None                     # Strife's API; filled in by bind()


def bind(api):
    globals().update(api)


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


def draw_grid():
    box(0, GTOP, W, GBOT - GTOP, "#fbfcfe")
    for gx in range(-1, 16):
        px, _ = to_px(gx, 0)
        box(px, GTOP, 1, GBOT - GTOP, "#dde3ea")
    for gy in range(-1, 7):
        _, py = to_px(0, gy)
        box(0, py, W, 1, "#dde3ea")
    box(OX - 1, GTOP, 2, GBOT - GTOP, "#495057")           # axes
    box(0, OY - 1, W, 2, "#495057")
    for gx in range(2, 16, 2):
        px, py = to_px(gx, 0)
        Draw.text(str(gx), px - 4, min(py + 5, GBOT - 18), 14, "#6c757d")
    for gy in range(1, 7):
        px, py = to_px(0, gy)
        Draw.text(str(gy), px - 16, py - 8, 14, "#6c757d")


def draw_walls(lv):
    for (x1, y1, x2, y2) in lv["walls"]:
        ax, ay = to_px(x1, y2)
        bx, by = to_px(x2, y1)
        box(ax, ay, bx - ax, by - ay, "#c92a2a")
        box(ax, ay, bx - ax, 3, "#e03131")


def draw_road(lv):
    """The player's function: bold between start and flag, faded outside."""
    ys, sx, gx_ = S["ys"], lv["start"][0], lv["goal"][0]
    for px in range(W - 1):
        a, b = ys[px] if px < len(ys) else None, ys[px + 1] if px + 1 < len(ys) else None
        if a is None or b is None:
            continue
        inside = sx <= to_x(px) <= gx_
        top_y = min(a, b)
        box(px, int(top_y) - 1, 2, int(abs(a - b)) + 3, "#1971c2" if inside else "#a5c8f0")


def draw_markers(lv):
    fx, fy = to_px(*lv["goal"])                            # checkpoint flag
    box(fx - 1, fy - 42, 3, 42, "#212529")
    box(fx + 2, fy - 42, 22, 14, "#2f9e44")
    box(fx - 4, fy - 4, 9, 9, "#2f9e44")
    sx_, sy_ = to_px(*lv["start"])                         # start marker
    box(sx_ - 4, sy_ - 4, 9, 9, "#f08c00")


def draw_vehicle():
    if S["mode"] == "crashed" and S["crash"]:
        cx, cy = to_px(*S["crash"])
        Draw.text("X", cx - 9, cy - 22, 34, "#c92a2a")
    else:
        cx, cy = to_px(S["cx"], S["cy"])
        draw_car(cx, cy)


def scene():
    lv = LEVELS[S["level"]]
    draw_grid()
    draw_walls(lv)
    draw_road(lv)
    draw_markers(lv)
    draw_vehicle()
