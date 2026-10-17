"""Level data. Teammates can add levels here without touching the game code.

Coordinates are graph units (x right, y up).
  start : the car's starting point. The road must pass through it.
  goal  : the checkpoint flag. The road must reach it.
  walls : obstacles as (x1, y1, x2, y2). The road may not touch them.
  solution : a known-good answer (used by the tests; hidden from players).
"""
LEVELS = [
    {
        "name": "1. Straight Road",
        "concept": "slope + intercept",
        "hint": "A line y = mx + b. Where does it start (b)? How steep must it climb (m)?",
        "start": (0, 1), "goal": (10, 4), "walls": [],
        "solution": "0.3x + 1",
    },
    {
        "name": "2. Over the Roadblock",
        "concept": "steeper slope",
        "hint": "The wall is in the way. A steeper line clears it, but you still have to hit the flag.",
        "start": (0, 0.5), "goal": (12, 5.5), "walls": [(5, 0, 6, 2.4)],
        "solution": "5/12 x + 0.5",
    },
    {
        "name": "3. Canyon Jump",
        "concept": "quadratics",
        "hint": "Start and goal are at the same height, but a straight road falls into the pit. Try a parabola.",
        "start": (0, 0), "goal": (10, 0),
        "walls": [(2, -1, 8, 0.8), (3, 3.5, 7, 6)],
        "solution": "-0.1x(x-10)",
    },
    {
        "name": "4. Mountain Slalom",
        "concept": "sine waves",
        "hint": "Weave between the blocks. Amplitude sets the height, the number in front of x sets how often it repeats.",
        "start": (0, 2.5), "goal": (12, 2.5),
        "walls": [(0.6, -1, 1.4, 3.2), (2.6, 2.6, 3.4, 6), (4.6, -1, 5.4, 3.2),
                  (6.6, 2.6, 7.4, 6), (8.6, -1, 9.4, 3.2), (10.6, 2.6, 11.4, 6)],
        "solution": "2.5 + 1.5sin(pi x / 2)",
    },
    {
        "name": "5. Bridge Builders",
        "concept": "linear functions",
        "hint": "A steady uphill line clears the first barrier, then stays below the second one.",
        "start": (0, 0), "goal": (14, 5.6),
        "walls": [(4, -1, 5, 1.0), (9, 4.2, 10, 6)],
        "solution": "0.4x",
    },
    {
        "name": "6. Parabola Pass",
        "concept": "quadratics",
        "hint": "The road must rise over the long barrier, then come back down to the flag. Use a parabola with zeros just beyond the endpoints.",
        "start": (0, 1), "goal": (12, 1),
        "walls": [(2, -1, 10, 2.3), (5, 4.1, 7, 6)],
        "solution": "-0.08x(x-12) + 1",
    },
    {
        "name": "7. Wave Tunnel",
        "concept": "sine waves",
        "hint": "Follow the alternating gaps. The road begins on its middle line, so start with a vertical shift of 2.",
        "start": (0, 2), "goal": (12, 2),
        "walls": [(0.7, -1, 1.3, 2.7), (2.7, 1.3, 3.3, 6),
                  (4.7, -1, 5.3, 2.7), (6.7, 1.3, 7.3, 6),
                  (8.7, -1, 9.3, 2.7), (10.7, 1.3, 11.3, 6)],
        "solution": "2 + 1.25sin(pi x / 2)",
    },
    {
        "name": "8. Curving Descent",
        "concept": "reciprocal functions",
        "hint": "A reciprocal curve can fall quickly and then flatten out. Keep its vertical asymptote safely to the left of the map.",
        "start": (0, 4), "goal": (12, 2.4),
        "walls": [(2, 3.5, 5, 6), (7, -1, 10, 2.2)],
        "solution": "2 + 6/(x + 3)",
    },
    {
        "name": "9. Downhill Detour",
        "concept": "linear functions",
        "hint": "This time the line slopes downward. Use the start and goal to find both the slope and the intercept.",
        "start": (0, 4), "goal": (12, 1),
        "walls": [(4, -1, 5, 2.4), (7, 2.5, 8, 6), (10, -1, 11, 1.1)],
        "solution": "-0.25x + 4",
    },
    {
        "name": "10. Valley Run",
        "concept": "quadratics",
        "hint": "The flag is at the same height as the start, but the safe route dips through a narrow valley before climbing back out.",
        "start": (0, 3.44), "goal": (14, 3.44),
        "walls": [(3, 2, 11, 6), (5, -1, 9, 0.2)],
        "solution": "0.06(x-7)^2 + 0.5",
    },
]
