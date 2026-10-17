# Road Trip: Function Junction (Strife! project)

Install: put this `RoadTrip` folder inside Strife's `projects/` folder, open Strife, click RoadTrip.
Or from a terminal: `python3 strife.py RoadTrip`

Play: pick a level, click the "y =" box, type a function (plots live), press Enter or Drive!

Files (one per teammate):
- scripts/mathparse.py : equation parser (no eval), supports 2x, x^2, sin(x), pi, abs, sqrt ...
- scripts/levels.py    : level data (start, goal, walls, hint). Add a level = add a dict.
- scripts/main.py      : game loop, graph drawing, car, UI
