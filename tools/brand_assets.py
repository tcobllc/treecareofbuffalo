# Cuts every logo raster the site ships from one transparent master PNG of the final badge:
#   assets/logo.png          256x256 RGBA  (header brand, pagehead badge, JSON-LD logo)
#   favicon-32.png            32x32 RGBA
#   icon-192.png             192x192 RGBA  (manifest)
#   icon-512.png             512x512 RGBA  (manifest)
#   apple-touch-icon.png     180x180 opaque on the surface color (iOS ignores alpha and would paint black)
# The master should be the badge on a transparent ground with its own margins trimmed; this script
# trims any fully transparent border, pads to a square with a small safe margin, and resizes with
# Lanczos. Run the gate and regenerate the Open Graph cards (tools/og_cards.py) afterwards.
#
#   python tools/brand_assets.py path\to\badge-master.png [--margin 0.04] [--surface #0f1a13]
import argparse, os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [("assets/logo.png", 256, False), ("favicon-32.png", 32, False), ("icon-192.png", 192, False),
           ("icon-512.png", 512, False), ("apple-touch-icon.png", 180, True)]

def square(im, margin):
    im = im.convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    side = int(max(w, h) * (1 + 2 * margin))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2), im)
    return canvas

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("master")
    ap.add_argument("--margin", type=float, default=0.04)
    ap.add_argument("--surface", default="#0f1a13")
    a = ap.parse_args()
    src = square(Image.open(a.master), a.margin)
    for rel, size, opaque in TARGETS:
        out = src.resize((size, size), Image.LANCZOS)
        if opaque:
            bg = Image.new("RGBA", (size, size), a.surface)
            bg.alpha_composite(out)
            out = bg.convert("RGB")
        path = os.path.join(ROOT, rel)
        out.save(path, optimize=True)
        print(f"wrote {rel} {size}x{size} {'opaque' if opaque else 'alpha'} {os.path.getsize(path)} bytes")
    print("next: python tools/og_cards.py  then  python tools/gate.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())
