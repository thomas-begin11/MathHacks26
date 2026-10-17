"""Numbers and coordinate helpers shared by every module. Change layout here."""
W, H = 960, 540                 # window size (fixed by Strife)
GTOP, GBOT = 50, 460            # the graph occupies y = 50..460 on screen
SCALE = 60                      # pixels per graph unit
OX, OY = 60, 420                # screen position of graph point (0, 0)
SPEED = 4.0                     # car speed, graph units per second
TOL = 0.35                      # how close to the flag counts as reaching it
START_TOL = 0.3                 # how close the road must pass to the car's start


def to_px(x, y):
    """Graph units -> screen pixels."""
    return OX + x * SCALE, OY - y * SCALE


def to_x(px):
    """Screen pixel column -> graph x."""
    return (px - OX) / SCALE
