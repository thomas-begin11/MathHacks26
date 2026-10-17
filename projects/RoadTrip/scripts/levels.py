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
]
