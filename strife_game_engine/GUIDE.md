# Strife! Guide

Strife! is a small engine for building screens, apps, and games. You can build the look **visually** (builder mode), add behavior in **Lua** or **Python**, or both. Everything goes through one shared API, so the Lua and Python versions of the same idea look almost identical.

**Pick your path:**

- [I just want to design screens (no code)](#1-using-the-builder-no-code)
- [I'll script in Lua](#2-scripting-in-lua)
- [I'll script in Python](#3-scripting-in-python)
- [Export your project as an app](#4-exporting-your-project-as-an-app)
- [Full API reference](#5-api-reference) (same for both languages)
- [Troubleshooting](#6-troubleshooting)

---

## 0. The basics

### Projects

A project is a folder with everything for one app:

```
projects/MyProject/
├── scripts/      main.lua and/or main.py (your code)
├── layouts/      screens saved by the builder (JSON, one per page)
├── assets/       images, and fonts/ for .ttf and .otf files
└── save.json     data saved with Storage.Save
```

- Launch Strife and click a project to open it.
- **F2** (inside a project) returns to the project list.
- **To make a project:** open any project, press **F1** (builder mode), then press **N**. Type a name, press **Tab** to switch between Lua and Python, and press **Enter**.
- From a terminal you can also run `python3 strife.py MyProject` to open one directly, or `python3 strife.py new MyProject py` to create one.

If you're using the packaged app, your projects live in **Documents/Strife/projects**.

### Hot reload

Keep the app open and edit your script or layout files in any editor. Save, and the running app updates within half a second. If your script has an error, a **red banner** appears at the bottom of the window instead of crashing, so fix the mistake, save again, and carry on.

### The window

The window is 960 × 540. The top-left corner is (0, 0), x grows to the right, and y grows downward.

---

## 1. Using the builder (no code)

Press **F1** to toggle builder mode. A bar appears at the bottom with the shortcuts. While you build, the app's game logic is paused and buttons don't fire.

### Add things

| Key | Adds |
|---|---|
| **B** | Button |
| **L** | Label (text) |
| **F** | Frame (a rectangle, good for panels and backgrounds) |
| **U** | Text box |

### Move, resize, and style

- **Click** a widget to select it. **Drag** it to move it. Arrow keys nudge it by 1 pixel (hold **Shift** for 10).
- A selected widget shows **handles**:
  - **Corner square:** drag to resize. On a label it becomes a dot that changes the text size.
  - **Top dot:** drag sideways to change corner rounding.
  - **Side dot:** drag up or down to change opacity. A percentage appears next to it.
- Shortcuts for the selected widget:

| Key | Action |
|---|---|
| **T** | Edit its text (Enter to finish, Esc to stop) |
| **I** | Give it an ID (used by scripts to find it) |
| **C** | Cycle the fill color (the text color on labels) |
| **V** | Cycle the text color |
| **H** | Type a text color: `#rrggbb` or a name like `red` (Enter applies it, Esc cancels) |
| **K** | Type a fill color the same way |
| **O** | Cycle through your imported fonts |
| **+ / -** | Change text size (labels) |
| **D** | Duplicate |
| **Delete** | Remove |
| **Z / X** | Move it forward / backward one layer (hold **Shift** to jump to the very front / back) |

### Pages

A project can have several screens, called pages.

- **Cmd/Ctrl + N** makes a new page (`page2`, `page3`, ...).
- **[** and **]** switch between pages.

### Save

Press **Cmd/Ctrl + S**. The current page is saved to `layouts/<page name>.json` and loads automatically every time the project opens.

> **Important:** Save before you edit a script file. Saving a script reloads the app, and anything you built but did not save is lost.

Widgets that a script created (not the builder) get an **orange** outline. You can move them to experiment, but they aren't saved, because the script owns them.

### Fonts, images, and themes

- **Drag a `.ttf` or `.otf` file onto the window** to import it. It is copied into the project, becomes the default font, and is remembered. Press **O** on a widget to give it a different imported font.
- **Drag an image** (png, jpg, bmp, gif) onto the window to copy it into `assets/`. Scripts can then show it with `UI.Image("name.png", x, y)`.
- Press **M** to preview the **modern theme** (rounded corners). To turn it on permanently, add `Theme.Set("modern")` to a script.

### What the builder can't do on its own

The builder makes the *look* of your screens. To make a button actually do something, such as open another page, you need a tiny script. It's two lines, shown in the next two sections.

---

## 2. Scripting in Lua

Your code lives in `scripts/main.lua`. It runs from top to bottom when the project opens, and again on every hot reload.

### A first script

```lua
Page.Open("main")

local title = UI.Text("Hello!", 40, 40, 32)
local btn = UI.Button("Click me", 40, 120, 200, 56)

local clicks = 0
btn.on_click = function()
  clicks = clicks + 1
  btn.text = "Clicked " .. clicks
end
```

Widgets are created on the **current page**, so call `Page.Open("name")` first.

### Wiring up a screen from the builder

Say you built a page called `Menu` with a button whose ID is `play`:

```lua
Page.Open("Menu")
UI.Load("Menu")                       -- optional: layouts also load by themselves

UI.Get("play").on_click = function()
  Page.Open("Game")
end
```

### Calling style

- Functions on `UI`, `Page`, `Storage`, and so on use a **dot**: `UI.Button(...)`, `Page.Open("x")`.
- Methods on a widget use a **colon**: `btn:destroy()`.
- Properties use a dot: `btn.text = "Hi"`, `player.x = player.x + 5`.
- Colors are **hex strings or names**: `"#ff8800"`, `"blue"`. (Tuples are Python only.)

### Game loop

Define these global functions and the engine calls them:

```lua
function on_update(dt)        -- every frame; dt is seconds since the last frame
  if Input.key_down("right") then player.x = player.x + 300 * dt end
end

function on_draw()            -- every frame, after widgets; use Draw.* here
  Draw.rect(10, 10, 100, 20, "red")
end
```

### More examples

```lua
-- Animate: slide a title in over 0.6 seconds
local title = UI.Text("Strife!", 400, -60, 48)
Tween(title, "y", 100, 0.6)

-- Run something later
After(2, function() title.text = "Ready" end)

-- Text box
local name = UI.Input("your name", 100, 200, 240, 40)
name.on_submit = function(text) print("hello " .. text) end

-- Save and load (numbers, strings, true/false)
Storage.Save("score", 10)
local score = Storage.Load("score", 0)

-- Collisions
if Overlaps(player, coin) then coin:destroy() end
```

Lua's `os.date` works too, for example `os.date("%H:%M")` for a clock. In Lua, `print` writes to the terminal when you launch from one.

### Colors and layers (Lua)

```lua
-- Text color: the "color" property. Button/frame/textbox fill: the "bg" property.
local title = UI.Text("Score", 40, 40, 32)
title.color = "#ffcc00"           -- hex, or a name: white black red green blue yellow gray dark panel

local btn = UI.Button("Play", 40, 100, 200, 56)
btn.bg = "#2a9d8f"                -- button fill
btn.color = "white"               -- button label
btn.alpha = 0.8                   -- 0 = invisible, 1 = solid (affects the whole widget)

-- Layers: higher z draws on top (and gets clicks first). Default is 0.
local shadow = UI.Frame(50, 50, 200, 100)
local card   = UI.Frame(40, 40, 200, 100)
shadow.z = 0
card.z = 1                        -- card sits above shadow

-- Draw.* (inside on_draw) draws after all widgets, so it appears on top of them
function on_draw()
  Draw.text("always on top", 10, 10, 20, "#ff5555")
end
```

Colors are one color per widget. To get two colors in one sentence, use two text widgets side by side.

---

## 3. Scripting in Python

Your code lives in `scripts/main.py`. It also runs top to bottom on load and on every hot reload. You do not import anything: `UI`, `Page`, `Tween`, and the rest are already available.

### A first script

```python
Page.Open("main")

title = UI.Text("Hello!", 40, 40, 32)
btn = UI.Button("Click me", 40, 120, 200, 56)

clicks = 0

def on_click():
    global clicks          # needed to change a module-level variable
    clicks += 1
    btn.text = f"Clicked {clicks}"

btn.on_click = on_click
```

Widgets are created on the **current page**, so call `Page.Open("name")` first.

### Wiring up a screen from the builder

```python
Page.Open("Menu")
UI.Load("Menu")                                   # optional: layouts also load by themselves

UI.Get("play").on_click = lambda: Page.Open("Game")
```

### Differences from Lua

- Methods and properties both use a dot: `btn.destroy()`, `btn.text = "Hi"`.
- Colors can be hex strings, names, **or `(r, g, b)` tuples**.
- `Storage.Save` can store Python lists and dicts as well as numbers, strings, and booleans.
- You can `import` the standard modules `math`, `random`, `time`, `datetime`, `collections`, `itertools`, `functools`, `string`, `statistics`, and `heapq`. You can also put extra `.py` files in `scripts/` and import them. In the packaged app, other third-party libraries are not available.
- If both `main.lua` and `main.py` exist, **both run**, so a team can mix languages in one project. Use different page names so they don't collide.

### Game loop

Define these module-level functions:

```python
def on_update(dt):                  # every frame; dt is seconds since the last frame
    if Input.key_down("right"):
        player.x += 300 * dt

def on_draw():                      # every frame, after widgets; use Draw.* here
    Draw.rect(10, 10, 100, 20, "red")
```

### More examples

```python
# Animate: slide a title in over 0.6 seconds
title = UI.Text("Strife!", 400, -60, 48)
Tween(title, "y", 100, 0.6)

# Run something later
After(2, lambda: setattr(title, "text", "Ready"))

# Text box
name = UI.Input("your name", 100, 200, 240, 40)
name.on_submit = lambda text: print("hello", text)

# Save and load
Storage.Save("score", 10)
score = Storage.Load("score", 0)

# Collisions
if Overlaps(player, coin):
    coin.destroy()
```

### Colors and layers (Python)

```python
# Text color: the "color" property. Button/frame/textbox fill: the "bg" property.
title = UI.Text("Score", 40, 40, 32)
title.color = "#ffcc00"           # hex, a name (white black red green blue yellow gray dark panel), or (r, g, b)

btn = UI.Button("Play", 40, 100, 200, 56)
btn.bg = (42, 157, 143)           # button fill
btn.color = "white"               # button label
btn.alpha = 0.8                   # 0 = invisible, 1 = solid (affects the whole widget)

# Layers: higher z draws on top (and gets clicks first). Default is 0.
shadow = UI.Frame(50, 50, 200, 100)
card = UI.Frame(40, 40, 200, 100)
shadow.z = 0
card.z = 1                        # card sits above shadow

# Draw.* (inside on_draw) draws after all widgets, so it appears on top of them
def on_draw():
    Draw.text("always on top", 10, 10, 20, "#ff5555")
```

Colors are one color per widget. To get two colors in one sentence, use two text widgets side by side.

---

## 4. Exporting your project as an app

An exported app runs **one project** and nothing else: **no builder, no project list, no hot reload, no red error banner**. F1 and F2 do nothing. Your scripts, layouts, images, and fonts are packed inside. This is the version you hand to other people.

### How to export

- **From the builder:** open your project, press **F1**, then **Cmd/Ctrl + E**. The status bar tells you when it's done (a few minutes the first time).
- **From a terminal:**

```
python3 export_app.py MyProject
python3 export_app.py MyProject --name "My App" --icon my_icon.png
```

Where the result lands:

| System | Result in the `dist/` folder |
|---|---|
| Mac | `My App.app` and `My App.dmg` (drag-to-Applications disk image) |
| Windows | `My App/My App.exe` (zip the whole folder to share it) |
| Linux | `My App/My App` |

Mac apps must be exported on a Mac and Windows apps on Windows.

### Good to know

- **Test it first, without building:** `python3 strife.py --play MyProject` runs the project exactly like an exported app.
- **Saved data** (`Storage.Save`) goes to the player's own folder, so they keep their progress: Mac `~/Library/Application Support/<App Name>`, Windows `%APPDATA%\<App Name>`. Your own `save.json` from development is **not** included, so players start fresh.
- **Closing the app:** Esc does not close it. Add a button that calls `Quit()`, or players can use the window's close button.
- **The app's name and icon:** the `--name` and `--icon` options (icon = a square PNG, 1024 x 1024 works best). The default icon is `icon.png`.
- **Your default font** (the one you dropped in) travels with the app.
- **Python scripts** in the app can import `math`, `random`, `time`, `datetime`, `collections`, `itertools`, `functools`, `string`, `statistics`, and `heapq`, plus your own `.py` files in `scripts/`.
- **First launch on another Mac:** unsigned apps show a warning. Right-click the app, choose **Open**, then **Open** again, once.
- **Exporting needs the Python version of Strife.** The packaged Strife editor app can't export; use `export_app.py` from the source folder.

---

## 5. API reference

Names are identical in Lua and Python.

### Creating widgets (on the current page)

| Call | Makes |
|---|---|
| `UI.Frame(x, y, w, h)` | A filled rectangle |
| `UI.Text(text, x, y, size)` | A text label |
| `UI.Button(text, x, y, w, h)` | A clickable button |
| `UI.Input(placeholder, x, y, w, h)` | A text box |
| `UI.Image(name, x, y, scale)` | An image from `assets/` |
| `UI.Get(id)` | Finds a widget by its ID (or nothing) |
| `UI.Load(name)` | Loads `layouts/<name>.json` into the current page |
| `UI.Destroy(widget)` or `widget:destroy()` | Removes a widget |

### Widget properties

You can read and change all of these at any time:

| Property | Meaning |
|---|---|
| `x`, `y` | Position |
| `w`, `h` | Size (not used by text labels, which size to their text) |
| `text` | Text on labels, buttons, and text boxes |
| `size` | Text size (labels) |
| `color` | Text color |
| `bg` | Fill color of frames, buttons, and text boxes |
| `alpha` | Opacity from 0 to 1 |
| `scale` | Image scale |
| `rounding` | Corner rounding from 0 to 1 (`-1` follows the theme) |
| `z` | Layer: higher numbers draw on top and get clicks first (default 0). Widgets with the same `z` stack in the order they were created. |
| `font` | Name of an imported font (`""` = default) |
| `visible` | `true`/`false` (Lua) or `True`/`False` (Python) |
| `id` | Name used by `UI.Get` |
| `on_click` | Function called when a button is clicked |
| `on_submit` | Function called with the text when Enter is pressed in a text box |

**Colors:** `"#rrggbb"` or one of `white black red green blue yellow gray dark panel`. (Python also accepts `(r, g, b)`.)

### Pages

| Call | Does |
|---|---|
| `Page.Open("name")` | Shows a page (creating it if needed). Widgets you create afterward go on it. |
| `Page.Close()` | Goes back to the previous page |
| `Page.Current()` | Returns the current page name |

### Animation and time

| Call | Does |
|---|---|
| `Tween(widget, "prop", target, seconds, ease, on_done)` | Smoothly changes a number property. `ease` is `"out"` (default), `"linear"`, or `"inout"`. `seconds`, `ease`, and `on_done` are optional. |
| `After(seconds, fn)` | Runs `fn` once, later |

### Input

| Call | Returns |
|---|---|
| `Input.key_down("space")` | True while the key is held |
| `Input.key_pressed("space")` | True only on the frame it was pressed |
| `Input.mouse_x()`, `Input.mouse_y()` | Mouse position |
| `Input.mouse_down()` | True while the left button is held |

Key names are lowercase: letters (`"a"`), `"space"`, `"enter"`, `"escape"`, `"tab"`, `"left"`, `"right"`, `"up"`, `"down"`, `"left_shift"`, and so on. For number keys use words: `"one"`, `"two"`, `"three"`.

### Drawing (inside `on_draw` only)

| Call | Draws |
|---|---|
| `Draw.rect(x, y, w, h, color)` | A rectangle |
| `Draw.text(text, x, y, size, color)` | Text |
| `Draw.image(name, x, y, scale)` | An image |

### Everything else

| Call | Does |
|---|---|
| `Storage.Save(key, value)` | Saves a value to the project's `save.json` |
| `Storage.Load(key, default)` | Reads it back |
| `Assets.Load(name)` | Preloads an image |
| `Font.Load("Name.ttf", size)` | Loads a font from `assets/fonts/` (default size 48) |
| `Font.SetDefault("Name.ttf")` | Uses that font everywhere by default |
| `Theme.Set("modern")` / `Theme.Set("classic")` | Rounded corners on or off |
| `Overlaps(a, b)` | True if two widgets overlap |
| `Quit()` | Closes the app (use it for an Exit button) |

---

## 6. Troubleshooting

**Red banner at the bottom.** Your script has an error. Read the message, fix the file, save, and it reloads.

**Blank window.** The project has no widgets yet. Check that `scripts/main.lua` or `main.py` is inside the project's `scripts/` folder and that you called `Page.Open(...)` for the page you want to see. Press F1 and look for pages with `[` and `]`.

**Things I built disappeared.** You edited a script before saving the builder. Press **Cmd/Ctrl+S** first, every time.

**Clicks land in the wrong spot.** In `strife.py`, set `HIDPI = False` near the top. (The packaged app needs a rebuild after this change.)

**A button does nothing.** The builder only draws buttons. Give the button an ID with **I**, then attach behavior in a script with `UI.Get("id").on_click = ...`.

**A font looks wrong or letters are missing.** Imported fonts load with basic English characters only.

**Esc doesn't close the window.** That's intentional, because the builder uses Esc. Use the window's close button.

**Can't find my files (packaged app).** Open the **Documents/Strife** folder. Projects are in `projects/`, and this guide is there too.

**My text color didn't change.** Text color is the `color` property. The `bg` property is the fill behind it. In the builder, press **H** to type a text color and **K** to type a fill color.

**A widget is hidden behind another one.** Raise its `z` (in the builder, select it and press **Z**, or **Shift+Z** to bring it to the very front).

**Export failed.** Open `export.log` next to `strife.py` to see why. The usual cause is not running inside your virtual environment: run `source .venv/bin/activate` first.

**The exported app opens but is blank or crashes.** Run `python3 strife.py --play MyProject` in a terminal first. If it fails there, the project has an error; the message will print in the terminal.
