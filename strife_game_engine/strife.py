"""Strife! Engine - single-file skeleton.
Run:  python3 strife.py     (loads scripts/main.lua and/or scripts/main.py)
Needs: pip install raylib lupa
Press F1 in the running window for builder mode.
"""
import os, sys, json, copy, shutil, re, subprocess, ctypes
from types import SimpleNamespace
import pyray as rl
from lupa import LuaRuntime
import math, random, time, datetime, collections, itertools, functools, string, statistics, heapq  # noqa: F401 (bundled so Python scripts can import them in the packaged app)

# ---------- paths (work both from source and when frozen by PyInstaller) ----------
BUNDLED = os.path.join(getattr(sys, "_MEIPASS", ""), "project")
PLAYER = bool(getattr(sys, "frozen", False) and os.path.isdir(BUNDLED))  # an exported app: runs one project, no editor
if PLAYER:
    BASE = BUNDLED
elif getattr(sys, "frozen", False):  # the Strife app: user files live in Documents/Strife, not inside the app
    BASE = os.path.join(os.path.expanduser("~"), "Documents", "Strife")
    os.makedirs(BASE, exist_ok=True)
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(BASE, "scripts")
ASSETS = os.path.join(BASE, "assets")
FONTS = os.path.join(ASSETS, "fonts")
LAYOUTS = os.path.join(BASE, "layouts")
SAVE_FILE = os.path.join(BASE, "save.json")
WIDTH, HEIGHT = 960, 540
EDIT_BAR = 70
HIDPI = True  # sharper on Retina. If mouse clicks land in the wrong place, set this to False.
PROJECTS = os.path.join(BASE, "projects")
DEFAULT_ROUND = {"frame": 0.06, "button": 0.35, "input": 0.25}  # corner rounding when the modern theme is on


def load_touchpad_pinch():
    """Load the optional macOS bridge for real trackpad magnify gestures."""
    if sys.platform != "darwin":
        return None
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "libstrife_touchpad.dylib")
    if not os.path.exists(path):
        return None
    try:
        bridge = ctypes.CDLL(path)
        bridge.strife_enable_touchpad_pinch()
        bridge.strife_take_touchpad_pinch.restype = ctypes.c_double
        return bridge
    except OSError:
        return None

def set_root(root, save_dir=None):
    """Point the engine at a project folder (scripts, layouts, assets). save_dir = where save.json goes."""
    global SCRIPTS, ASSETS, FONTS, LAYOUTS, SAVE_FILE
    SCRIPTS, ASSETS = os.path.join(root, "scripts"), os.path.join(root, "assets")
    FONTS, LAYOUTS = os.path.join(ASSETS, "fonts"), os.path.join(root, "layouts")
    SAVE_FILE = os.path.join(save_dir or root, "save.json")

def set_project(name):
    set_root(os.path.join(PROJECTS, name))

def user_data_dir(app_name):
    """Where an exported app keeps its save file (the app bundle itself is read-only)."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    elif sys.platform.startswith("win"):
        base = os.environ.get("APPDATA", home)
    else:
        base = os.path.join(home, ".local", "share")
    folder = os.path.join(base, re.sub(r"[^A-Za-z0-9 _-]", "", app_name) or "StrifeApp")
    os.makedirs(folder, exist_ok=True)
    return folder

LUA_TEMPLATE = """-- Strife starter (Lua). F1 = builder, F2 = project list.
Page.Open("main")
local title = UI.Text("Hello from Strife!", 40, 40, 32)
local btn = UI.Button("Click me", 40, 120, 200, 56)
local clicks = 0
btn.on_click = function()
  clicks = clicks + 1
  btn.text = "Clicked " .. clicks
end

function on_update(dt)
  -- game logic goes here (it pauses while the builder is open)
end
"""

PY_TEMPLATE = """# Strife starter (Python). F1 = builder, F2 = project list.
Page.Open("main")
title = UI.Text("Hello from Strife!", 40, 40, 32)
btn = UI.Button("Click me", 40, 120, 200, 56)
clicks = 0

def on_click():
    global clicks
    clicks += 1
    btn.text = f"Clicked {clicks}"

btn.on_click = on_click

def on_update(dt):
    pass  # game logic goes here (it pauses while the builder is open)
"""

# ---------- colors: "#rrggbb", a name, or (r, g, b) ----------
NAMED = {
    "white": (255, 255, 255), "black": (0, 0, 0), "red": (230, 60, 60),
    "green": (60, 200, 90), "blue": (60, 120, 230), "yellow": (240, 210, 60),
    "gray": (130, 130, 130), "dark": (28, 28, 38), "panel": (52, 54, 74),
}
PALETTE = ["panel", "blue", "green", "red", "yellow", "gray", "white", "black", "dark"]
FIELDS = ["kind", "id", "x", "y", "w", "h", "text", "size", "color", "bg",
          "alpha", "scale", "image", "placeholder", "font", "rounding", "z", "visible"]

def color(c, alpha=1.0):
    if isinstance(c, str):
        if c.startswith("#") and len(c) == 7:
            r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        else:
            r, g, b = NAMED.get(c.lower(), (255, 255, 255))
    else:
        r, g, b = c
    return rl.Color(int(r), int(g), int(b), int(255 * max(0.0, min(1.0, alpha))))

# ---------- easing ----------
EASE = {
    "linear": lambda t: t,
    "out": lambda t: 1 - (1 - t) ** 3,
    "inout": lambda t: 3 * t * t - 2 * t * t * t,
}


class Widget:
    """One object for every UI element. kind = frame | text | button | image | input."""
    engine = None

    def __init__(self, kind, x=0, y=0, w=0, h=0, text="", size=20):
        self.kind, self.x, self.y, self.w, self.h = kind, x, y, w, h
        self.text, self.size, self.id, self.placeholder = text, size, "", ""
        self.font = ""  # "" = the default font
        self.rounding = -1  # corner rounding 0..1, or -1 to follow the theme
        self.z = 0  # layer: higher z draws on top (same z: later-created is on top)
        self.color, self.bg = "white", "panel"
        self.alpha, self.scale = 1.0, 1.0
        self.visible, self.hover = True, False
        self.on_click = None
        self.on_submit = None
        self.image = None
        self.layout = ""  # name of the layout file this widget is saved in ("" = made by a script)

    def contains(self, mx, my):
        return self.x <= mx <= self.x + self.w and self.y <= my <= self.y + self.h

    def destroy(self):
        Widget.engine.remove(self)


class Engine:
    def __init__(self):
        Widget.engine = self
        self.pages, self.current, self.history = {"main": []}, "main", []
        self.tweens, self.timers, self.textures, self.hooks = [], [], {}, []
        self.error = ""
        self.mtime, self.reload_timer = 0, 0.0
        self.lua = None
        self.save = {}
        self.edit, self.sel, self.drag, self.typing = False, None, None, None
        self.loaded_layouts, self.page_tags = set(), {}
        self.status, self.status_t = "", 0.0
        self.fonts, self.default_font, self.theme = {}, "", "classic"
        self.hub, self.start = False, None
        self.player, self.project, self.app_font = PLAYER, "", ""
        self.exporting, self.quitting, self.typing_old = None, False, None
        self.touchpad = None
        self.newproj = SimpleNamespace(name="", lang="lua", on_submit=None)
        self.newproj.on_submit = lambda *_: self.create_project(self.newproj.name, self.newproj.lang)
        if os.path.exists(SAVE_FILE):
            try:
                self.save = json.load(open(SAVE_FILE))
            except Exception:
                self.save = {}
        self.default_font = self.save.get("__default_font", "")

    # ---------- error handling: never crash the window, show the error instead ----------
    def safe(self, fn, *args):
        try:
            return fn(*args)
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            print("[strife]", self.error)

    # ---------- the one API, shared by Lua and Python ----------
    def build_api(self):
        def add(w):
            self.pages[self.current].append(w)
            return w

        def get(wid):
            for w in self.pages.get(self.current, []):
                if w.id == wid:
                    return w
            for ws in self.pages.values():
                for w in ws:
                    if w.id == wid:
                        return w
            return None

        ui = SimpleNamespace(
            Frame=lambda x=0, y=0, w=100, h=100: add(Widget("frame", x, y, w, h)),
            Text=lambda text="", x=0, y=0, size=20: add(Widget("text", x, y, 0, size, text, size)),
            Button=lambda text="", x=0, y=0, w=160, h=48: add(Widget("button", x, y, w, h, text)),
            Input=lambda placeholder="", x=0, y=0, w=240, h=40: self._input(add, placeholder, x, y, w, h),
            Image=lambda name, x=0, y=0, scale=1.0: self._image(add, name, x, y, scale),
            Get=get,
            Destroy=lambda w: self.remove(w),
            Load=lambda name: self.load_layout(name),
        )

        def page_open(name):
            self.pages.setdefault(name, [])
            if name != self.current:
                self.history.append(self.current)
            self.current = name

        def page_close():
            if self.history:
                self.current = self.history.pop()

        page = SimpleNamespace(Open=page_open, Close=page_close, Current=lambda: self.current)

        def tween(obj, prop, target, seconds=0.4, ease="out", on_done=None):
            self.tweens.append([obj, prop, float(getattr(obj, prop)), float(target),
                                max(seconds, 0.001), 0.0, EASE.get(ease, EASE["out"]), on_done])

        def storage_save(key, value):
            self.save[key] = value
            json.dump(self.save, open(SAVE_FILE, "w"))

        storage = SimpleNamespace(Save=storage_save, Load=lambda key, default=None: self.save.get(key, default))
        assets = SimpleNamespace(Load=lambda name: self._tex(name) and name)

        def key_of(name):
            return getattr(rl, "KEY_" + str(name).upper(), None)

        def pinch():
            if self.touchpad:
                return self.touchpad.strife_take_touchpad_pinch() * 8
            return (1 if rl.get_gesture_detected() == rl.GESTURE_PINCH_IN else
                    -1 if rl.get_gesture_detected() == rl.GESTURE_PINCH_OUT else 0)

        inp = SimpleNamespace(
            key_down=lambda k: bool(key_of(k) and rl.is_key_down(key_of(k))),
            key_pressed=lambda k: bool(key_of(k) and rl.is_key_pressed(key_of(k))),
            mouse_x=lambda: rl.get_mouse_x(),
            mouse_y=lambda: rl.get_mouse_y(),
            mouse_down=lambda: rl.is_mouse_button_down(rl.MOUSE_BUTTON_LEFT),
            mouse_pressed=lambda: rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT),
            mouse_wheel=lambda: rl.get_mouse_wheel_move(),
            pinch=pinch,
        )

        window = SimpleNamespace(
            width=lambda: rl.get_screen_width(),
            height=lambda: rl.get_screen_height(),
            fullscreen=lambda: rl.is_window_fullscreen(),
            toggle_fullscreen=lambda: rl.toggle_fullscreen(),
        )

        draw = SimpleNamespace(  # only valid inside on_draw()
            rect=lambda x, y, w, h, c="white": rl.draw_rectangle(int(x), int(y), int(w), int(h), color(c)),
            text=lambda t, x, y, size=20, c="white": self.draw_str(None, t, x, y, size, color(c)),
            image=lambda name, x, y, scale=1.0: self._draw_image(name, x, y, scale, 1.0),
        )

        def set_default_font(name):
            if name not in self.fonts:
                self.load_font(name)
            self.default_font = name

        font = SimpleNamespace(Load=lambda name, size=48: self.load_font(name, size), SetDefault=set_default_font)
        theme = SimpleNamespace(Set=lambda name: setattr(self, "theme", "modern" if name == "modern" else "classic"),
                                Get=lambda: self.theme)

        def after(seconds, fn):
            self.timers.append([float(seconds), fn])

        def overlaps(a, b):
            aw, ah = self.size_of(a)
            bw, bh = self.size_of(b)
            return a.x < b.x + bw and b.x < a.x + aw and a.y < b.y + bh and b.y < a.y + ah

        return {"UI": ui, "Page": page, "Tween": tween, "Storage": storage, "Assets": assets,
                "Input": inp, "Draw": draw, "After": after, "Overlaps": overlaps,
                "Font": font, "Theme": theme, "Window": window,
                "Quit": lambda: setattr(self, "quitting", True)}

    # ---------- assets ----------
    def _tex(self, name):
        if name not in self.textures:
            path = os.path.join(ASSETS, name)
            tex = rl.load_texture(path)
            self.textures[name] = tex if tex.id != 0 else None
        return self.textures[name]

    def _image(self, add, name, x, y, scale):
        tex = self._tex(name)
        w = Widget("image", x, y, tex.width * scale if tex else 0, tex.height * scale if tex else 0)
        w.image, w.scale = name, scale
        return add(w)

    def _input(self, add, placeholder, x, y, w, h):
        wd = Widget("input", x, y, w, h)
        wd.placeholder = placeholder
        return add(wd)

    def _draw_image(self, name, x, y, scale, alpha):
        tex = self._tex(name)
        if tex:
            rl.draw_texture_ex(tex, rl.Vector2(x, y), 0.0, scale, color("white", alpha))

    # ---------- widget helpers ----------
    def size_of(self, w):
        if w.kind == "text":
            return self.text_w(w, w.text, w.size), int(w.size)
        return w.w, w.h

    def ordered(self):
        return sorted(self.pages.get(self.current, []), key=lambda w: w.z)

    def remove(self, w):
        for ws in self.pages.values():
            if w in ws:
                ws.remove(w)
        self.tweens = [t for t in self.tweens if t[0] is not w]
        if self.sel is w:
            self.sel = None
        if self.typing and self.typing[0] is w:
            self.typing = None

    # ---------- fonts, themes, drag-and-drop import ----------
    def font_of(self, w=None):
        return self.fonts.get((w.font if w and w.font else "") or self.default_font)

    def draw_str(self, w, text, x, y, size, col):
        f = self.font_of(w)
        if f:
            rl.draw_text_ex(f, str(text), rl.Vector2(int(x), int(y)), float(size), 0.0, col)
        else:
            rl.draw_text(str(text), int(x), int(y), int(size), col)

    def text_w(self, w, text, size):
        f = self.font_of(w)
        if f:
            return rl.measure_text_ex(f, str(text), float(size), 0.0).x
        return rl.measure_text(str(text), int(size))

    def rad(self, w, default):
        return w.rounding if w.rounding >= 0 else (default if self.theme == "modern" else 0.0)

    def box(self, x, y, w, h, col, r=0.0):
        if r > 0:
            rl.draw_rectangle_rounded(rl.Rectangle(x, y, w, h), r, 8, col)
        else:
            rl.draw_rectangle(int(x), int(y), int(w), int(h), col)

    def load_font(self, name, size=48):
        if name in self.fonts:
            return name
        for folder in (FONTS, ASSETS):
            path = os.path.join(folder, name)
            if os.path.exists(path):
                f = rl.load_font_ex(path, int(size), None, 0)
                rl.set_texture_filter(f.texture, rl.TEXTURE_FILTER_BILINEAR)
                self.fonts[name] = f
                return name
        raise FileNotFoundError("font not found in assets/fonts: " + str(name))

    def load_font_dir(self):
        if os.path.isdir(FONTS):
            for f in sorted(os.listdir(FONTS)):
                if os.path.splitext(f)[1].lower() in (".ttf", ".otf"):
                    self.safe(self.load_font, f)

    def handle_drops(self):
        """Drag a .ttf/.otf (or an image) onto the window to import it into assets/."""
        if self.player or not rl.is_file_dropped():
            return
        files = rl.load_dropped_files()
        paths = [rl.ffi.string(files.paths[i]).decode() for i in range(files.count)]
        rl.unload_dropped_files(files)
        if self.hub:
            self.status, self.status_t = "Open a project first, then drop files in", 3.0
            return
        for p in paths:
            name, ext = os.path.basename(p), os.path.splitext(p)[1].lower()
            if ext in (".ttf", ".otf"):
                os.makedirs(FONTS, exist_ok=True)
                shutil.copy(p, os.path.join(FONTS, name))
                self.load_font(name)
                self.default_font = name
                self.save["__default_font"] = name
                json.dump(self.save, open(SAVE_FILE, "w"))
                self.status, self.status_t = f"Imported font {name} (now the default font)", 3.0
            elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
                os.makedirs(ASSETS, exist_ok=True)
                shutil.copy(p, os.path.join(ASSETS, name))
                self.status, self.status_t = f"Imported image {name}: use UI.Image('{name}', x, y)", 4.0

    # ---------- projects ----------
    def export_app(self):
        """Builder: Cmd/Ctrl+E packages the open project as a standalone app (needs the Python version of Strife)."""
        script = os.path.join(BASE, "export_app.py")
        if getattr(sys, "frozen", False):
            msg = "Export needs the Python version: run  python3 export_app.py <project>"
        elif self.exporting and self.exporting.poll() is None:
            msg = "Already exporting, please wait"
        elif not self.project:
            msg = "Open a project first"
        elif not os.path.exists(script):
            msg = "export_app.py was not found next to strife.py"
        else:
            log = open(os.path.join(BASE, "export.log"), "w")
            self.exporting = subprocess.Popen([sys.executable, script, self.project], cwd=BASE,
                                              stdout=log, stderr=subprocess.STDOUT)
            msg = f"Exporting '{self.project}' ... this takes a few minutes. Result goes in dist/"
        self.status, self.status_t = msg, 6.0

    def seed_bundle(self):
        """Packaged app: put the guide next to the user's projects on first run."""
        src = os.path.join(getattr(sys, "_MEIPASS", ""), "GUIDE.md")
        dst = os.path.join(BASE, "GUIDE.md")
        if getattr(sys, "frozen", False) and os.path.exists(src) and not os.path.exists(dst):
            shutil.copy(src, dst)

    def migrate_legacy(self):
        """Older single-project layout (scripts/ next to strife.py) becomes projects/demo."""
        legacy, target = os.path.join(BASE, "scripts"), os.path.join(PROJECTS, "demo")
        if os.path.isdir(legacy) and not os.path.exists(target):
            os.makedirs(target)
            for sub in ("scripts", "layouts", "assets"):
                if os.path.isdir(os.path.join(BASE, sub)):
                    shutil.copytree(os.path.join(BASE, sub), os.path.join(target, sub))

    def make_project(self, name, lang="lua"):
        name = re.sub(r"[^A-Za-z0-9_-]", "", name or "")[:30]
        if not name:
            self.status, self.status_t = "Type a project name first", 3.0
            return None
        root = os.path.join(PROJECTS, name)
        if os.path.exists(root):
            self.status, self.status_t = f"'{name}' already exists", 3.0
            return None
        for sub in ("scripts", "layouts", os.path.join("assets", "fonts")):
            os.makedirs(os.path.join(root, sub))
        py = str(lang).lower().startswith("py")
        with open(os.path.join(root, "scripts", "main.py" if py else "main.lua"), "w", encoding="utf-8") as f:
            f.write(PY_TEMPLATE if py else LUA_TEMPLATE)
        return name

    def create_project(self, name, lang):
        made = self.make_project(name, lang)
        if made:
            self.open_project(made)

    def open_project(self, name):
        if name:
            set_project(name)
            self.project = name
        sys.path[:] = [p for p in sys.path if not p.startswith(PROJECTS)]
        self.textures, self.fonts, self.theme = {}, {}, "classic"
        try:
            self.save = json.load(open(SAVE_FILE)) if os.path.exists(SAVE_FILE) else {}
        except Exception:
            self.save = {}
        self.default_font = self.save.get("__default_font", "") or self.app_font
        self.hub = False
        self.load_font_dir()
        self.load_scripts()

    def build_hub(self):
        """The project picker, built from the engine's own widgets."""
        self.hub, self.edit, self.default_font, self.theme = True, False, "", "classic"
        self.hooks, self.tweens, self.timers = [], [], []
        self.sel = self.drag = self.typing = None
        self.pages, self.current, self.history = {"hub": []}, "hub", []
        ws = self.pages["hub"]
        ws.append(Widget("text", 330, 40, 0, 44, "Strife!", 44))
        sub = Widget("text", 330, 100, 0, 18, "Choose a project", 18)
        sub.color = "gray"
        ws.append(sub)
        def listing():
            return sorted(d for d in os.listdir(PROJECTS) if os.path.isdir(os.path.join(PROJECTS, d))) \
                if os.path.isdir(PROJECTS) else []
        names = listing()
        if not names:  # first launch: make one so there is something to open
            self.make_project("Starter", "lua")
            names = listing()
        for i, n in enumerate(names[:7]):
            b = Widget("button", 330, 130 + i * 52, 300, 44, n)
            b.on_click = lambda n=n: self.open_project(n)
            ws.append(b)
        if len(names) > 7:
            more = Widget("text", 330, 490, 0, 14, f"+{len(names) - 7} more: python3 strife.py <name>", 14)
            more.color = "gray"
            ws.append(more)
        hint = Widget("text", 330, 510, 0, 13, "In a project: F1 builder, N new project, F2 this list", 13)
        hint.color = "gray"
        ws.append(hint)
        where = Widget("text", 330, 526, 0, 12, "Files: " + BASE, 12)
        where.color = "gray"
        ws.append(where)

    # ---------- layouts (JSON files made by builder mode) ----------
    def load_layout(self, name):
        path = os.path.join(LAYOUTS, name + ".json")
        if not os.path.exists(path):
            return 0
        data = json.load(open(path, encoding="utf-8"))
        self.loaded_layouts.add(name)
        self.page_tags.setdefault(self.current, set()).add(name)
        count = 0
        for d in data.get("widgets", []):
            if d.get("kind") == "image":
                w = self._image(lambda wd: wd, d.get("image", ""), d.get("x", 0), d.get("y", 0), d.get("scale", 1.0))
            else:
                w = Widget(d.get("kind", "frame"))
            for k in FIELDS:
                if k in d:
                    setattr(w, k, d[k])
            w.layout = name
            self.pages[self.current].append(w)
            count += 1
        return count

    def autoload_layouts(self):
        """Layouts no script asked for still show up, on the page with the same name."""
        if not os.path.isdir(LAYOUTS):
            return
        cur = self.current
        for f in sorted(os.listdir(LAYOUTS)):
            name, ext = os.path.splitext(f)
            if ext == ".json" and name not in self.loaded_layouts:
                self.pages.setdefault(name, [])
                self.current = name
                self.load_layout(name)
        self.current = cur

    def save_layout(self):
        os.makedirs(LAYOUTS, exist_ok=True)
        groups = {t: [] for t in self.page_tags.get(self.current, set())}
        for w in self.pages[self.current]:
            if w.layout:
                groups.setdefault(w.layout, []).append(
                    {k: (round(getattr(w, k)) if k in ("x", "y", "w", "h") else getattr(w, k)) for k in FIELDS})
        for tag, items in groups.items():
            with open(os.path.join(LAYOUTS, tag + ".json"), "w", encoding="utf-8") as f:
                json.dump({"widgets": items}, f, indent=2)
        self.status, self.status_t = "Saved: " + ", ".join(f"layouts/{t}.json" for t in groups), 3.0

    # ---------- script loading + hot reload ----------
    def scan_mtime(self):
        newest = 0
        for base in (SCRIPTS, LAYOUTS):
            for root, _, files in os.walk(base):
                for f in files:
                    newest = max(newest, os.path.getmtime(os.path.join(root, f)))
        return newest

    def load_scripts(self):
        keep = self.current
        self.pages, self.current, self.history = {"main": []}, "main", []
        self.tweens, self.timers, self.hooks, self.error = [], [], [], ""
        self.sel, self.drag, self.typing = None, None, None
        self.loaded_layouts, self.page_tags = set(), {}
        self.mtime = self.scan_mtime()
        api = self.build_api()

        lua_main = os.path.join(SCRIPTS, "main.lua")
        py_main = os.path.join(SCRIPTS, "main.py")

        if os.path.exists(lua_main):
            self.lua = LuaRuntime(unpack_returned_tuples=True)
            self.lua.execute(f"package.path = [[{SCRIPTS.replace(chr(92), '/')}/?.lua;]] .. package.path")
            g = self.lua.globals()
            for name, obj in api.items():
                g[name] = obj
            self.safe(lambda: self.lua.execute(open(lua_main, encoding="utf-8").read()))
            for hook in ("on_update", "on_draw"):
                if g[hook]:
                    self.hooks.append((hook, g[hook]))

        if os.path.exists(py_main):
            if SCRIPTS not in sys.path:
                sys.path.insert(0, SCRIPTS)
            ns = dict(api, __name__="strife_script")
            self.safe(lambda: exec(compile(open(py_main, encoding="utf-8").read(), py_main, "exec"), ns))
            for hook in ("on_update", "on_draw"):
                if callable(ns.get(hook)):
                    self.hooks.append((hook, ns[hook]))

        self.safe(self.autoload_layouts)

        if keep != "main" and keep in self.pages:  # stay on the page you were editing
            self.current = keep

    # ---------- typing (text boxes and builder text editing) ----------
    def handle_typing(self):
        chars = []
        while True:  # always drain, so stray keypresses never pile up
            ch = rl.get_char_pressed()
            if ch == 0:
                break
            chars.append(chr(ch))
        if not self.typing:
            return False
        w, attr = self.typing
        s = str(getattr(w, attr)) + "".join(c for c in chars if c.isprintable())
        if rl.is_key_pressed(rl.KEY_BACKSPACE) or rl.is_key_pressed_repeat(rl.KEY_BACKSPACE):
            s = s[:-1]
        setattr(w, attr, s)
        if w is self.newproj and rl.is_key_pressed(rl.KEY_TAB):
            w.lang = "py" if w.lang == "lua" else "lua"
        if rl.is_key_pressed(rl.KEY_ENTER):
            self.end_typing(False)
            if (not self.edit or w is self.newproj) and w.on_submit:
                self.safe(w.on_submit, getattr(w, "text", ""))
        elif rl.is_key_pressed(rl.KEY_ESCAPE):
            self.end_typing(True)
        return True

    def end_typing(self, cancel):
        if self.typing_old:  # typing a color: keep it only if it is valid
            w, attr, old = self.typing_old
            v = str(getattr(w, attr)).lower()
            if cancel or not (v in NAMED or re.fullmatch(r"#[0-9a-f]{6}", v)):
                setattr(w, attr, old)
                if not cancel:
                    self.status, self.status_t = "Use #rrggbb or a color name; kept the old color", 3.0
            self.typing_old = None
        self.typing = None

    # ---------- builder mode ----------
    def spawn(self, kind):
        n = len(self.pages[self.current]) * 10 % 120
        w = {"button": lambda: Widget("button", 100 + n, 100 + n, 160, 48, "Button"),
             "text": lambda: Widget("text", 100 + n, 100 + n, 0, 24, "Text", 24),
             "frame": lambda: Widget("frame", 100 + n, 100 + n, 200, 120),
             "input": lambda: Widget("input", 100 + n, 100 + n, 240, 40)}[kind]()
        w.layout = self.current
        self.page_tags.setdefault(self.current, set()).add(self.current)
        self.pages[self.current].append(w)
        self.sel = w

    def cycle(self, w, attr):
        cur = getattr(w, attr)
        i = PALETTE.index(cur) if cur in PALETTE else -1
        setattr(w, attr, PALETTE[(i + 1) % len(PALETTE)])

    def edit_keys(self):
        kp = lambda k: rl.is_key_pressed(k) or rl.is_key_pressed_repeat(k)
        mod = any(rl.is_key_down(k) for k in (rl.KEY_LEFT_CONTROL, rl.KEY_RIGHT_CONTROL,
                                               rl.KEY_LEFT_SUPER, rl.KEY_RIGHT_SUPER))
        if mod and rl.is_key_pressed(rl.KEY_S):
            self.save_layout()
            return
        if mod and rl.is_key_pressed(rl.KEY_E):
            self.export_app()
            return
        if mod and rl.is_key_pressed(rl.KEY_N):
            n = 2
            while f"page{n}" in self.pages:
                n += 1
            self.pages[f"page{n}"] = []
            self.current, self.sel = f"page{n}", None
            return
        if rl.is_key_pressed(rl.KEY_N):
            self.newproj.name = ""
            self.typing = (self.newproj, "name")
            return
        names = list(self.pages)
        if rl.is_key_pressed(rl.KEY_LEFT_BRACKET) or rl.is_key_pressed(rl.KEY_RIGHT_BRACKET):
            step = -1 if rl.is_key_pressed(rl.KEY_LEFT_BRACKET) else 1
            self.current, self.sel = names[(names.index(self.current) + step) % len(names)], None
            return
        if rl.is_key_pressed(rl.KEY_M):
            self.theme = "modern" if self.theme == "classic" else "classic"
            self.status, self.status_t = f"Theme: {self.theme} (scripts set it with Theme.Set)", 2.5
            return
        for key, kind in ((rl.KEY_B, "button"), (rl.KEY_L, "text"), (rl.KEY_F, "frame"), (rl.KEY_U, "input")):
            if rl.is_key_pressed(key):
                self.spawn(kind)
                return
        s = self.sel
        if not s:
            return
        step = 10 if (rl.is_key_down(rl.KEY_LEFT_SHIFT) or rl.is_key_down(rl.KEY_RIGHT_SHIFT)) else 1
        if kp(rl.KEY_LEFT): s.x -= step
        if kp(rl.KEY_RIGHT): s.x += step
        if kp(rl.KEY_UP): s.y -= step
        if kp(rl.KEY_DOWN): s.y += step
        if rl.is_key_pressed(rl.KEY_DELETE) or rl.is_key_pressed(rl.KEY_BACKSPACE):
            s.destroy()
            return
        if rl.is_key_pressed(rl.KEY_T) and s.kind in ("text", "button", "input"):
            self.typing = (s, "text")
        if rl.is_key_pressed(rl.KEY_I):
            self.typing = (s, "id")
        if rl.is_key_pressed(rl.KEY_C):
            self.cycle(s, "color" if s.kind == "text" else "bg")
        if rl.is_key_pressed(rl.KEY_V):
            self.cycle(s, "color")
        if not mod and (rl.is_key_pressed(rl.KEY_H) or rl.is_key_pressed(rl.KEY_K)):
            attr = "color" if rl.is_key_pressed(rl.KEY_H) else "bg"
            self.typing_old = (s, attr, getattr(s, attr))
            setattr(s, attr, "#")
            self.typing = (s, attr)
        if not mod and (rl.is_key_pressed(rl.KEY_Z) or rl.is_key_pressed(rl.KEY_X)):
            up = rl.is_key_pressed(rl.KEY_Z)
            zs = [w.z for w in self.pages[self.current]]
            if step == 10:  # Shift: all the way to the front / back
                s.z = (max(zs) + 1) if up else (min(zs) - 1)
            else:
                s.z += 1 if up else -1
            self.status, self.status_t = f"layer {s.z:g}", 1.5
        if rl.is_key_pressed(rl.KEY_O):
            opts = [""] + sorted(self.fonts)
            s.font = opts[(opts.index(s.font) + 1) % len(opts)] if s.font in opts else ""
            self.status, self.status_t = f"font: {s.font or 'default'}", 1.5
        if s.kind == "text" and kp(rl.KEY_EQUAL):
            s.size = min(120, s.size + 2)
        if s.kind == "text" and kp(rl.KEY_MINUS):
            s.size = max(8, s.size - 2)
        if rl.is_key_pressed(rl.KEY_D):
            d = copy.copy(s)
            d.id, d.x, d.y = "", s.x + 20, s.y + 20
            self.pages[self.current].append(d)
            self.sel = d

    def handles(self, s):
        """Draggable handles on the selected widget: opacity, corner rounding, resize / text size."""
        sw, sh = self.size_of(s)
        hs = {"alpha": (s.x + sw + 14, s.y + (1 - s.alpha) * max(sh, 40))}
        hs["size" if s.kind == "text" else "resize"] = (s.x + sw, s.y + sh)
        if s.kind in DEFAULT_ROUND:
            hs["round"] = (s.x + self.rad(s, DEFAULT_ROUND[s.kind]) * min(sw, sh) / 2, s.y)
        return hs

    def edit_mouse(self, mx, my, clicked):
        down = rl.is_mouse_button_down(rl.MOUSE_BUTTON_LEFT)
        if clicked and my < HEIGHT - EDIT_BAR:
            self.end_typing(False)
            if self.sel:
                for mode, (hx, hy) in self.handles(self.sel).items():
                    if abs(mx - hx) <= 8 and abs(my - hy) <= 8:
                        self.drag = (mode, 0, 0)
                        break
            if not self.drag:
                self.sel = None
                for w in reversed(self.ordered()):
                    sw, sh = self.size_of(w)
                    if w.visible and w.x <= mx <= w.x + sw and w.y <= my <= w.y + sh:
                        self.sel = w
                        self.drag = ("move", mx - w.x, my - w.y)
                        break
        if self.drag and self.sel:
            if not down:
                self.drag = None
            elif self.drag[0] == "move":
                self.sel.x, self.sel.y = round(mx - self.drag[1]), round(my - self.drag[2])
            else:
                s = self.sel
                sw, sh = self.size_of(s)
                mode = self.drag[0]
                if mode == "resize":
                    s.w, s.h = max(10, round(mx - s.x)), max(10, round(my - s.y))
                elif mode == "size":
                    s.size = max(8, min(120, round(my - s.y)))
                elif mode == "alpha":
                    s.alpha = round(max(0.05, min(1.0, 1 - (my - s.y) / max(sh, 40))), 2)
                elif mode == "round":
                    s.rounding = round(max(0.0, min(1.0, (mx - s.x) / max(min(sw, sh) / 2, 1))), 2)
        elif self.drag:
            self.drag = None

    def draw_edit(self):
        for w in self.pages.get(self.current, []):
            sw, sh = self.size_of(w)
            rl.draw_rectangle_lines(int(w.x), int(w.y), int(sw), int(sh), color("gray", 0.5))
        s = self.sel
        if s:
            sw, sh = self.size_of(s)
            c = color("#3c9cff") if s.layout else color("#ff9a3c")
            rl.draw_rectangle_lines(int(s.x) - 1, int(s.y) - 1, int(sw) + 2, int(sh) + 2, c)
            tl = max(sh, 40)
            rl.draw_line(int(s.x + sw + 14), int(s.y), int(s.x + sw + 14), int(s.y + tl), color("gray", 0.6))
            for mode, (hx, hy) in self.handles(s).items():
                if mode == "resize":
                    rl.draw_rectangle(int(hx) - 5, int(hy) - 5, 10, 10, c)
                else:
                    rl.draw_circle(int(hx), int(hy), 5, c)
            rl.draw_text(f"{int(s.alpha * 100)}%", int(s.x + sw + 24), int(s.y + (1 - s.alpha) * tl) - 6, 12, color("white"))
        by = HEIGHT - EDIT_BAR
        rl.draw_rectangle(0, by, WIDTH, EDIT_BAR, color("black", 0.85))
        if self.typing and self.typing[0] is self.newproj:
            n = self.newproj
            line = f"NEW PROJECT: {n.name}_   [{'Python' if n.lang == 'py' else 'Lua'}]   Tab = switch language, Enter = create, Esc = cancel"
        elif self.typing:
            line = f"TYPING into {self.typing[1]} - Enter to finish, Esc to stop"
        elif s:
            sw, sh = self.size_of(s)
            line = f"EDIT page '{self.current}' | {s.kind} id='{s.id}' layer={s.z:g} x={int(s.x)} y={int(s.y)} w={int(sw)} h={int(sh)}"
            if not s.layout:
                line += "  (made by a script: moves here, but is not saved)"
        else:
            line = f"EDIT MODE - page '{self.current}' - click a widget or press B / L / F / U to add one"
        if self.status_t > 0:
            line = self.status
        rl.draw_text(line, 8, by + 6, 16, color("yellow"))
        rl.draw_text("F1 exit  F2 projects  N new project | B button  L label  F frame  U textbox | drag=move  corner=resize  top dot=rounding  side dot=opacity",
                     8, by + 26, 12, color("white"))
        rl.draw_text("T text  I id  C/V cycle fill/text color  H/K type text/fill color (#rrggbb or name)  O font  M theme  +/- size  D duplicate  Del remove",
                     8, by + 40, 12, color("white"))
        rl.draw_text("Z/X layer up/down (Shift = front/back)  [ ] pages | Cmd/Ctrl: S save   N new page   E export app",
                     8, by + 54, 12, color("white"))

    # ---------- per-frame ----------
    def update(self, dt):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = rl.get_screen_width(), rl.get_screen_height()
        self.reload_timer += dt
        self.status_t = max(0.0, self.status_t - dt)
        if self.reload_timer > 0.5:
            self.reload_timer = 0.0
            if not self.hub and not self.player and self.scan_mtime() != self.mtime:
                self.load_scripts()

        if self.exporting and self.exporting.poll() is not None:
            ok = self.exporting.returncode == 0
            self.status, self.status_t = ("Export finished: look in the dist folder" if ok else "Export failed: see export.log"), 10.0
            self.exporting = None
        self.safe(self.handle_drops)
        if rl.is_key_pressed(rl.KEY_F2) and not self.hub and not self.player:
            self.build_hub()
        was_typing = self.handle_typing()
        if rl.is_key_pressed(rl.KEY_F1) and not self.hub and not self.player:
            self.edit = not self.edit
            self.end_typing(True)
            self.sel, self.drag = None, None
        if self.edit and not was_typing:
            self.edit_keys()

        mx, my = rl.get_mouse_x(), rl.get_mouse_y()
        widgets = self.ordered()
        clicked = rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT)
        if self.edit:
            self.edit_mouse(mx, my, clicked)
        else:
            hit = False
            for w in reversed(widgets):
                if not w.visible or w.kind not in ("button", "input"):
                    continue
                w.hover = (not hit) and w.contains(mx, my)
                if w.hover and clicked:
                    if w.kind == "input":
                        self.typing = (w, "text")
                    elif w.on_click:
                        self.safe(w.on_click)
                hit = hit or w.hover
            if clicked and self.typing and self.typing[0].kind == "input" and not self.typing[0].hover:
                self.typing = None

        for tw in self.tweens[:]:
            obj, prop, start, target, dur, t, ease, done = tw
            if self.drag and obj is self.sel:
                continue
            tw[5] = t = min(t + dt, dur)
            setattr(obj, prop, start + (target - start) * ease(t / dur))
            if t >= dur:
                self.tweens.remove(tw)
                if done:
                    self.safe(done)

        for tm in self.timers[:]:
            tm[0] -= dt
            if tm[0] <= 0:
                self.timers.remove(tm)
                self.safe(tm[1])

        if not self.edit:  # game logic is frozen while you build
            for name, fn in self.hooks:
                if name == "on_update":
                    self.safe(fn, dt)

    def draw(self):
        for w in self.ordered():
            if not w.visible:
                continue
            if w.kind == "frame":
                self.box(w.x, w.y, w.w, w.h, color(w.bg, w.alpha), self.rad(w, 0.06))
            elif w.kind == "text":
                self.draw_str(w, w.text, w.x, w.y, w.size, color(w.color, w.alpha))
            elif w.kind == "button":
                bg = color(w.bg, w.alpha)
                if w.hover:
                    bg = rl.Color(min(bg.r + 30, 255), min(bg.g + 30, 255), min(bg.b + 30, 255), bg.a)
                self.box(w.x, w.y, w.w, w.h, bg, self.rad(w, 0.35))
                tw_ = self.text_w(w, w.text, 20)
                self.draw_str(w, w.text, w.x + (w.w - tw_) / 2, w.y + (w.h - 20) / 2, 20, color(w.color, w.alpha))
            elif w.kind == "input":
                focused = bool(self.typing and self.typing[0] is w)
                edge = color("blue" if focused else "gray", 1.0 if focused else 0.6)
                if self.rad(w, 0.25) > 0:
                    self.box(w.x - 2, w.y - 2, w.w + 4, w.h + 4, edge, self.rad(w, 0.25))
                    self.box(w.x, w.y, w.w, w.h, color(w.bg, w.alpha), self.rad(w, 0.25))
                else:
                    self.box(w.x, w.y, w.w, w.h, color(w.bg, w.alpha))
                    rl.draw_rectangle_lines(int(w.x), int(w.y), int(w.w), int(w.h), edge)
                has_text = bool(w.text) or focused
                shown = str(w.text) if has_text else str(w.placeholder)
                cursor = "|" if focused and int(rl.get_time() * 2) % 2 == 0 else ""
                self.draw_str(w, shown + cursor, w.x + 8, w.y + (w.h - 20) / 2, 20,
                              color(w.color if has_text else "gray", w.alpha))
            elif w.kind == "image":
                self._draw_image(w.image, w.x, w.y, w.scale, w.alpha)

        for name, fn in self.hooks:
            if name == "on_draw":
                self.safe(fn)

        if self.edit:
            self.draw_edit()
        elif self.status_t > 0:
            rl.draw_text(self.status, 10, 10, 16, color("yellow"))

        if self.error and not self.player:  # visible error banner so hot-reload mistakes are obvious
            ey = HEIGHT - 40 - (EDIT_BAR if self.edit else 0)
            rl.draw_rectangle(0, ey, WIDTH, 40, color("red", 0.85))
            rl.draw_text(self.error[:90], 10, ey + 12, 18, color("white"))

    def run(self):
        title = "Strife!"
        if PLAYER:  # exported app: the project is bundled inside, saves go to the user's data folder
            try:
                app = json.load(open(os.path.join(BUNDLED, "app.json")))
            except Exception:
                app = {}
            title, self.app_font = app.get("name", "Strife App"), app.get("font", "")
            set_root(BUNDLED, user_data_dir(title))
        else:
            self.seed_bundle()
        rl.set_config_flags(rl.FLAG_MSAA_4X_HINT | rl.FLAG_WINDOW_RESIZABLE |
                            (rl.FLAG_WINDOW_HIGHDPI if HIDPI else 0))
        rl.init_window(WIDTH, HEIGHT, title)
        self.touchpad = load_touchpad_pinch()
        rl.set_target_fps(60)
        rl.set_exit_key(rl.KEY_NULL)  # Esc is used by builder mode, not for quitting
        if PLAYER:
            self.open_project(None)
        else:
            self.migrate_legacy()
            if self.start and os.path.isdir(os.path.join(PROJECTS, self.start)):
                self.open_project(self.start)
            else:
                self.build_hub()
                if self.start:
                    self.status, self.status_t = f"Project '{self.start}' not found", 4.0
        while not rl.window_should_close() and not self.quitting:
            self.update(rl.get_frame_time())
            rl.begin_drawing()
            rl.clear_background(color("dark"))
            self.draw()
            rl.end_drawing()
        rl.close_window()


if __name__ == "__main__":
    eng = Engine()
    args = sys.argv[1:]
    if len(args) > 1 and args[0] == "new":  # python3 strife.py new MyGame [lua|py]
        eng.start = eng.make_project(args[1], args[2] if len(args) > 2 else "lua")
    elif len(args) > 1 and args[0] == "--play":  # python3 strife.py --play MyGame  (no builder, like an exported app)
        eng.start, eng.player = args[1], True
    elif args:  # python3 strife.py MyGame
        eng.start = args[0]
    eng.run()
