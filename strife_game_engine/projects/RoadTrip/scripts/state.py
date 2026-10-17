"""The one shared game-state dictionary. game.py changes it, draw.py reads it.

mode: "edit" (typing), "driving", "crashed" or "won"
f:    the parsed function for the current text (or None)
ys:   the road's screen height for every pixel column (None where undefined)
"""
S = dict(level=0, f=None, text="", err="", mode="edit", cx=0.0, cy=0.0, crash=None, ys=[])
