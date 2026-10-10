# Regenerates the 19 Open Graph cards (assets/og-card.jpg and assets/og/*.jpg, 1200x630) from the
# hero ending frame, the current badge (assets/logo.png or --badge <master.png>) and the real
# fonts. Every card shares one layout; CARDS holds each page's title and mono line(s). Run after
# tools/brand_assets.py whenever the badge changes, then tools/gate.py.
#
#   python tools/og_cards.py                 writes all cards in place
#   python tools/og_cards.py --out DIR       writes them somewhere else (to compare first)
#   python tools/og_cards.py --only home     one card
#   python tools/og_cards.py --analyze       measures the geometry of the shipped home card
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1200, 630
BACKDROP = os.path.join(ROOT, "assets", "hero-ending.jpg")
BEVAN = os.path.join(ROOT, "..", "build", "brand", "fonts", "bevan.woff")
MONO = os.path.join(ROOT, "assets", "fonts", "courier-prime-700-latin.woff2")
CREAM, AMBER, MUTED, INK = (245, 235, 214), (232, 150, 58), (203, 188, 157), (23, 13, 5)
SURFACE = (15, 26, 19)

TOWN_LINE = "REMOVAL · TRIMMING · STUMPS · STORM WORK"
CARDS = {
    "og-card": ("Tree Service in Buffalo, NY", [TOWN_LINE, "FULLY INSURED · FREE WRITTEN ESTIMATES"]),
    "tree-removal": ("Tree Removal in Buffalo, NY", ["RIGGED DOWN IN SECTIONS · YARD LEFT CLEAN"]),
    "tree-trimming-pruning": ("Tree Trimming in Buffalo, NY", ["CLEAN CUTS · HEALTHY TREES · CLEAR OF THE HOUSE"]),
    "stump-grinding": ("Stump Grinding in Buffalo, NY", ["GROUND BELOW GRADE · READY TO SEED"]),
    "land-clearing": ("Land Clearing in Buffalo, NY", ["LOTS · FENCE LINES · OVERGROWN CORNERS"]),
    "emergency-storm-work": ("Storm Damage? We Answer.", ["DOWN LIMBS · HANGERS · TREES ON STRUCTURES"]),
    "estimate": ("Get a Free Written Estimate", ["THE ESTIMATE IS THE PRICE · PAY ON COMPLETION"]),
    "faq": ("Straight Answers on Tree Work", ["INSURANCE · PRICING · CLEANUP · STORMS"]),
    "why-us": ("Ten Years in the Trees", ["FULLY INSURED · FREE WRITTEN ESTIMATES"]),
    "services": ("Tree Services in Buffalo, NY", ["REMOVAL · TRIMMING · STUMPS · CLEARING · STORM WORK"]),
    "service-area": ("Buffalo and Western New York", ["CHEEKTOWAGA · AMHERST · TONAWANDA · HAMBURG + MORE"]),
}
for town in ("Amherst", "Cheektowaga", "Hamburg", "Kenmore", "Lackawanna", "Orchard Park", "Tonawanda", "West Seneca"):
    CARDS[town.lower().replace(" ", "-")] = (f"Tree Service in {town}, NY", [TOWN_LINE])

# Geometry (pixels on the 1200x630 card). Tune with --analyze against the shipped card.
G = dict(badge_box=(82, 93, 258, 269), wordmark_xy=(300, 190), wordmark_size=88, of_xy=(304, 212), of_size=22, of_track=0.66,
         rule=(85, 330, 705), title_xy=(85, 415), title_size=44, line_y=(456, 510), line_size=21, line_track=0.25,
         chip=(85, 545, 500, 604), chip_radius=10, chip_text_size=34, chip_text_xy=(110, 588))
# xy values are left-baseline anchors

def load_fonts():
    return (ImageFont.truetype(BEVAN, G["wordmark_size"]), ImageFont.truetype(MONO, G["of_size"]),
            ImageFont.truetype(BEVAN, G["title_size"]), ImageFont.truetype(MONO, G["line_size"]), ImageFont.truetype(MONO, G["chip_text_size"]))

def backdrop():
    im = Image.open(BACKDROP).convert("RGB")
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x0, y0, x0 + W, y0 + H))
    # left-to-right and top-down darkening so the type sits on pine, not on grass
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = ov.load()
    for x in range(W):
        ax = max(0.0, 1 - x / 900) ** 1.0 * 0.90
        for y in range(H):
            ay = max(0.0, 1 - y / 330) * 0.18
            a = min(1.0, ax + ay + 0.14)
            px[x, y] = (SURFACE[0], SURFACE[1], SURFACE[2], int(a * 255))
    out = Image.alpha_composite(im.convert("RGBA"), ov)
    return out

def tracked_text(draw, xy, text, font, fill, track_em):
    x, y = xy
    gap = int(font.size * track_em)
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + gap

def render(key, badge_img, fonts, base):
    title, lines = CARDS[key]
    f_word, f_of, f_title, f_line, f_chip = fonts
    im = base.copy()
    d = ImageDraw.Draw(im)
    bx0, by0, bx1, by1 = G["badge_box"]
    b = badge_img.copy(); b.thumbnail((bx1 - bx0, by1 - by0), Image.LANCZOS)
    im.alpha_composite(b, (bx0 + ((bx1 - bx0) - b.width) // 2, by0 + ((by1 - by0) - b.height) // 2))
    d.text(G["wordmark_xy"], "Tree Care", font=f_word, fill=CREAM, anchor="ls")
    tracked_text(d, G["of_xy"], "OF BUFFALO", f_of, AMBER, G["of_track"])
    rx0, ry, rx1 = G["rule"]
    d.line([(rx0, ry), (rx1, ry)], fill=(74, 97, 82, 200), width=2)
    d.text(G["title_xy"], title, font=f_title, fill=CREAM, anchor="ls")
    for i, line in enumerate(lines[:2]):
        tracked_text(d, (G["title_xy"][0], G["line_y"][i]), line, f_line, MUTED, G["line_track"])
    cx0, cy0, cx1, cy1 = G["chip"]
    d.rounded_rectangle((cx0, cy0, cx1, cy1), radius=G["chip_radius"], fill=AMBER)
    d.text(G["chip_text_xy"], "(716) 601-8275", font=f_chip, fill=INK, anchor="ls")
    return im.convert("RGB")

def analyze():
    """Measure the shipped home card: badge bbox, chip bbox (amber mask), text row bands."""
    card = Image.open(os.path.join(ROOT, "assets", "og-card.jpg")).convert("RGB")
    bd = backdrop().convert("RGB")
    diff = ImageChops.difference(card, bd).convert("L").point(lambda v: 255 if v > 60 else 0)
    print("badge bbox (diff in the top-left 300x300):", diff.crop((0, 0, 300, 300)).getbbox())
    amber = Image.eval(ImageChops.difference(card, Image.new("RGB", card.size, AMBER)).convert("L"), lambda v: 255 if v < 40 else 0)
    print("chip bbox (amber mask, lower half):", tuple(v + (0 if i % 2 == 0 else 315) for i, v in enumerate(amber.crop((0, 315, 700, 630)).getbbox())))
    rows = [y for y in range(H) if diff.crop((280, y, 1000, y + 1)).getbbox()]
    bands, start = [], None
    for y in range(H):
        on = y in set(rows)
        if on and start is None: start = y
        if not on and start is not None: bands.append((start, y - 1)); start = None
    print("text row bands (x 280 to 1000):", bands)
    cols = [x for x in range(W) if diff.crop((x, 560, x + 1, 600)).getbbox()]
    print("bottom band columns with content:", (min(cols), max(cols)) if cols else None)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out"); ap.add_argument("--only"); ap.add_argument("--badge"); ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze(); return 0
    badge = Image.open(a.badge or os.path.join(ROOT, "assets", "logo.png")).convert("RGBA")
    fonts, base = load_fonts(), backdrop()
    keys = [a.only] if a.only else list(CARDS)
    for key in keys:
        im = render(key, badge, fonts, base)
        rel = "assets/og-card.jpg" if key == "og-card" else f"assets/og/{key}.jpg"
        path = os.path.join(a.out, os.path.basename(rel)) if a.out else os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        im.save(path, "JPEG", quality=86, optimize=True, progressive=True)
        print("wrote", path, os.path.getsize(path), "bytes")
    return 0

if __name__ == "__main__":
    sys.exit(main())
