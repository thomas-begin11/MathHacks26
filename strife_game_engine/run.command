#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
if [ "$(uname)" = "Darwin" ] && [ ! -f libstrife_touchpad.dylib ]; then
  clang -dynamiclib -fblocks -framework Cocoa pinch_touchpad.m -o libstrife_touchpad.dylib || exit 1
fi
python3 strife.py
