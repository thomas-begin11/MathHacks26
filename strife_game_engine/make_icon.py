"""Turns icon.png into icon.icns (Mac) and icon.ico (Windows). Run automatically by the build scripts."""
from PIL import Image

img = Image.open("icon.png").convert("RGBA")
img.save("icon.icns")
img.save("icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("made icon.icns and icon.ico")
