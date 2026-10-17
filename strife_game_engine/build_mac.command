#!/bin/bash
# Builds Strife.app and Strife.dmg. Run on a Mac:   bash build_mac.command
cd "$(dirname "$0")"
[ -d .venv ] && source .venv/bin/activate

python3 -m pip install --quiet pyinstaller pillow raylib lupa || exit 1
python3 make_icon.py || exit 1

rm -rf build dist
python3 -m PyInstaller --noconfirm --windowed --name Strife --icon icon.icns \
  --collect-all raylib --collect-all pyray --collect-all lupa --hidden-import _cffi_backend \
  --add-data "GUIDE.md:." strife.py || exit 1

# a drag-to-Applications disk image
rm -rf dmg && mkdir dmg
cp -R dist/Strife.app dmg/
ln -s /Applications dmg/Applications
hdiutil create -volname "Strife" -srcfolder dmg -ov -format UDZO dist/Strife.dmg
rm -rf dmg

echo
echo "Done:  dist/Strife.app   and   dist/Strife.dmg"
