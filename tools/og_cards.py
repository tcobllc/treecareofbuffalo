# Regenerates the 19 Open Graph cards (assets/og-card.jpg and assets/og/*.jpg, 1200x630).
# Layout: deep pine ground with a warm amber glow, the badge large on the right, and a text column on
# the left (kicker, two-line Bevan title, mono service line, amber phone chip) on one left edge and
# centered vertically. No photo backdrop. Run after tools/brand_assets.py whenever the badge changes,
# then tools/gate.py.
#
#   python tools/og_cards.py                 writes all cards in place
#   python tools/og_cards.py --out DIR       writes them somewhere else (to compare first)
#   python tools/og_cards.py --only home     one card ("home" or "og-card" is the site-wide card)
#   python tools/og_cards.py --badge PNG     use a transparent badge master instead of assets/logo.png
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 630
BEVAN = os.path.join(ROOT, "..", "build", "brand", "fonts", "bevan.woff")
MONO = os.path.join(ROOT, "assets", "fonts", "courier-prime-700-latin.woff2")
PINE, CREAM, MUTED, AMBER, INK = (15, 26, 19), (245, 235, 214), (203, 188, 157), (232, 150, 58), (23, 13, 5)
AMBER_MUTED, BORDER = (118, 69, 5), (45, 64, 51)
PHONE = "(716) 601-8275"
KICKER = "FULLY INSURED · FREE ESTIMATES"

TOWN_LINE = "REMOVAL · TRIMMING · STUMPS · STORMS"
# key: (title lines, service line)
CARDS = {
    "og-card": (["Tree Service", "in Buffalo, NY"], TOWN_LINE),
    "tree-removal": (["Tree Removal", "in Buffalo, NY"], "RIGGED DOWN IN SECTIONS · YARD LEFT CLEAN"),
    "tree-trimming-pruning": (["Tree Trimming", "in Buffalo, NY"], "CLEAN CUTS · HEALTHY TREES · CLEAR OF THE HOUSE"),
    "stump-grinding": (["Stump Grinding", "in Buffalo, NY"], "GROUND BELOW GRADE · READY TO SEED"),
    "land-clearing": (["Land Clearing", "in Buffalo, NY"], "LOTS · FENCE LINES · OVERGROWN CORNERS"),
    "emergency-storm-work": (["Storm Damage?", "We Answer."], "DOWN LIMBS · HANGERS · TREES ON STRUCTURES"),
    "estimate": (["Free Written", "Estimates"], "THE ESTIMATE IS THE PRICE · PAY ON COMPLETION"),
    "faq": (["Straight Answers", "on Tree Work"], "INSURANCE · PRICING · CLEANUP · STORMS"),
    "why-us": (["Ten Years", "in the Trees"], "MON-FRI 7 AM TO 7 PM · STORM CALLS ANYTIME"),
    "services": (["Tree Services", "in Buffalo, NY"], "REMOVAL · TRIMMING · STUMPS · CLEARING · STORMS"),
    "service-area": (["Buffalo and", "Western New York"], "CHEEKTOWAGA · AMHERST · TONAWANDA · HAMBURG + MORE"),
}
for town in ("Amherst", "Cheektowaga", "Hamburg", "Kenmore", "Lackawanna", "Orchard Park", "Tonawanda", "West Seneca"):
    CARDS[town.lower().replace(" ", "-")] = (["Tree Service", f"in {town}, NY"], TOWN_LINE)

# Geometry. The text column runs from X0 to X0 + COL; the badge is centered at BADGE_C.
X0, COL = 72, 560
BADGE_C, BADGE_MAX = (930, 315), 470
TITLE_SIZE, TITLE_LH, LINE_SIZE, KICKER_SIZE, PHONE_SIZE = 62, 74, 22, 22, 40
GAP_KICKER, GAP_TITLE, GAP_LINE, CHIP_H, CHIP_PAD = 28, 30, 36, 72, 28

def tlen(text, font, track):
    return sum(font.getlength(c) for c in text) + track * (len(text) - 1)

def tracked(d, x, y, text, font, fill, track):
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill, anchor="ls")
        x += font.getlength(ch) + track

def fit(text, path, size, track, width):
    """Shrink tracking, then size, until the line fits the column."""
    font = ImageFont.truetype(path, size)
    while tlen(text, font, track) > width and track > 0.5:
        track -= 0.25
    while tlen(text, font, track) > width:
        size -= 1
        font = ImageFont.truetype(path, size)
    return font, track

def glow(img, center, radius, color, strength):
    yy, xx = np.mgrid[0:H, 0:W]
    a = (np.clip(1 - np.hypot(xx - center[0], yy - center[1]) / radius, 0, 1) ** 2 * strength)[..., None]
    arr = np.asarray(img).astype(np.float32) * (1 - a) + np.array(color, np.float32) * a
    return Image.fromarray(arr.astype(np.uint8))

def ground():
    img = Image.new("RGB", (W, H), PINE)
    img = glow(img, BADGE_C, 520, AMBER_MUTED, 0.55)
    img = glow(img, BADGE_C, 260, AMBER, 0.10)
    noise = np.random.default_rng(1).normal(0, 4, (H, W, 1))
    img = Image.fromarray(np.clip(np.asarray(img).astype(np.float32) + noise, 0, 255).astype(np.uint8))
    ImageDraw.Draw(img).rectangle((0, 0, W - 1, H - 1), outline=BORDER, width=2)
    return img

def place_badge(img, badge):
    b = badge.copy()
    b.thumbnail((BADGE_MAX, BADGE_MAX), Image.LANCZOS)
    x, y = BADGE_C[0] - b.width // 2, BADGE_C[1] - b.height // 2
    shadow = Image.new("L", (W, H), 0)
    shadow.paste(b.split()[3], (x + 8, y + 14))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.6))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    layer.putalpha(shadow)
    img = img.convert("RGBA")
    img.alpha_composite(layer)
    img.alpha_composite(b, (x, y))
    return img

def render(key, badge, base):
    title, line = CARDS[key]
    img = place_badge(base.copy(), badge)
    d = ImageDraw.Draw(img)
    kf, ktr = fit(KICKER, MONO, KICKER_SIZE, 4.5, COL)
    lf, ltr = fit(line, MONO, LINE_SIZE, 3.0, COL)
    tf = ImageFont.truetype(BEVAN, TITLE_SIZE)
    while max(tf.getlength(t) for t in title) > COL:
        tf = ImageFont.truetype(BEVAN, tf.size - 2)
    pf = ImageFont.truetype(MONO, PHONE_SIZE)
    total = KICKER_SIZE + GAP_KICKER + TITLE_LH * len(title) + GAP_TITLE + LINE_SIZE + GAP_LINE + CHIP_H
    y = (H - total) // 2 + KICKER_SIZE
    tracked(d, X0, y, KICKER, kf, AMBER, ktr)
    y += GAP_KICKER
    for t in title:
        y += TITLE_LH
        d.text((X0, y - 12), t, font=tf, fill=CREAM, anchor="ls")
    y += GAP_TITLE + LINE_SIZE - 8
    tracked(d, X0, y, line, lf, MUTED, ltr)
    y += GAP_LINE
    pw = tlen(PHONE, pf, 1.5)
    d.rounded_rectangle((X0, y, X0 + pw + 2 * CHIP_PAD, y + CHIP_H), radius=10, fill=AMBER)
    tracked(d, X0 + CHIP_PAD, y + CHIP_H / 2 + 14, PHONE, pf, INK, 1.5)
    return img.convert("RGB")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out"); ap.add_argument("--only"); ap.add_argument("--badge")
    a = ap.parse_args()
    badge = Image.open(a.badge or os.path.join(ROOT, "assets", "logo.png")).convert("RGBA")
    base = ground()
    keys = ["og-card" if a.only == "home" else a.only] if a.only else list(CARDS)
    for key in keys:
        im = render(key, badge, base)
        rel = "assets/og-card.jpg" if key == "og-card" else f"assets/og/{key}.jpg"
        path = os.path.join(a.out, os.path.basename(rel)) if a.out else os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        im.save(path, "JPEG", quality=86, optimize=True, progressive=True)
        print("wrote", path, os.path.getsize(path), "bytes")
    return 0

if __name__ == "__main__":
    sys.exit(main())
