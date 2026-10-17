"""Export a Strife project as a standalone app: no builder, no project picker, no hot reload.

Usage:
    python3 export_app.py MyProject
    python3 export_app.py MyProject --name "My App" --icon my_icon.png

Result:
    Mac:      dist/<Name>.app and dist/<Name>.dmg
    Windows:  dist/<Name>/<Name>.exe   (zip the whole folder to share it)
    Linux:    dist/<Name>/<Name>

Mac apps must be built on a Mac and Windows apps on Windows.
You can also press Cmd/Ctrl+E in builder mode to run this for the open project.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser(description="Export a Strife project as a standalone app.")
    ap.add_argument("project", help="folder name inside projects/")
    ap.add_argument("--name", help="app name (default: the project name)")
    ap.add_argument("--icon", help="a square PNG to use as the app icon (default: icon.png)")
    args = ap.parse_args()

    src = os.path.join(HERE, "projects", args.project)
    if not os.path.isdir(src):
        sys.exit(f"No project folder found: {src}")
    name = args.name or args.project
    safe = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip() or "StrifeApp"

    needed = (("PyInstaller", "pyinstaller"), ("PIL", "pillow"), ("pyray", "raylib"), ("lupa", "lupa"))
    missing = [pkg for mod, pkg in needed if importlib.util.find_spec(mod) is None]
    if missing and subprocess.call([sys.executable, "-m", "pip", "install", "--quiet", *missing]) != 0:
        sys.exit("Could not install " + ", ".join(missing) + ".\n"
                 "Activate your virtual environment first (source .venv/bin/activate) and run this again.")

    work = os.path.join(HERE, "build_export")
    shutil.rmtree(work, ignore_errors=True)
    stage = os.path.join(work, "project")
    shutil.copytree(src, stage, ignore=shutil.ignore_patterns("save.json", "__pycache__", ".DS_Store"))

    # the default font you picked in the builder travels with the app
    font = ""
    try:
        font = json.load(open(os.path.join(src, "save.json"))).get("__default_font", "")
    except Exception:
        pass
    with open(os.path.join(stage, "app.json"), "w") as f:
        json.dump({"name": name, "font": font}, f)

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed", "--name", safe,
           "--distpath", os.path.join(HERE, "dist"),
           "--workpath", os.path.join(work, "pyi"),
           "--specpath", work,
           "--collect-all", "raylib", "--collect-all", "pyray", "--collect-all", "lupa",
           "--hidden-import", "_cffi_backend",
           "--add-data", stage + (";" if os.name == "nt" else ":") + "project"]

    if sys.platform == "darwin" or os.name == "nt":
        from PIL import Image
        icon_src = args.icon or os.path.join(HERE, "icon.png")
        icon_path = os.path.join(work, "icon." + ("icns" if sys.platform == "darwin" else "ico"))
        img = Image.open(icon_src).convert("RGBA")
        if os.name == "nt":
            img.save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        else:
            img.save(icon_path)
        cmd += ["--icon", icon_path]

    cmd.append(os.path.join(HERE, "strife.py"))
    subprocess.check_call(cmd)

    dist = os.path.join(HERE, "dist")
    if sys.platform == "darwin":
        dmg_dir = os.path.join(work, "dmg")
        os.makedirs(dmg_dir)
        shutil.copytree(os.path.join(dist, safe + ".app"), os.path.join(dmg_dir, safe + ".app"), symlinks=True)
        os.symlink("/Applications", os.path.join(dmg_dir, "Applications"))
        subprocess.check_call(["hdiutil", "create", "-volname", safe, "-srcfolder", dmg_dir,
                               "-ov", "-format", "UDZO", os.path.join(dist, safe + ".dmg")])
        print(f"\nDone: {os.path.join(dist, safe)}.app and .dmg")
    else:
        print(f"\nDone: {os.path.join(dist, safe)}")


if __name__ == "__main__":
    main()
