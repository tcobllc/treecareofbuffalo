# Pre-deploy gate for treecareofbuffalo-site.
# Run:  python tools/predeploy.py   (from the repo root; exits nonzero on any failure)
#
# Checks, in order:
#   1. devibe_scan.py (vendored, MIT, github.com/JCarterJohnson/vibecoded-design-tells)
#      gates on HIGH-severity AI-design tells only. The known MEDIUM "neon glow" hits
#      are the deliberate amber CTA halo + film vignettes; see DESIGN.md "Reviewed tells".
#   2. Zero em dashes in any shipped HTML.
#   3. NAP lockstep: only tel:+17166018275 and (716) 601-8275 formats appear.
#   4. No leftover booking.html hrefs (booking is a redirect stub).
#   5. Every canonical URL is absolute on https://treecareofbuffalo.com.

import io, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []

r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "devibe_scan.py"),
                    ROOT, "--severity", "high"], capture_output=True, text=True)
if r.returncode != 0:
    fails.append(f"devibe: {r.returncode} HIGH-severity design tells\n{r.stdout[-1200:]}")

for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "tools"}]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT)
        t = io.open(p, encoding="utf-8").read()
        if "—" in t:
            fails.append(f"em dash in {rel}")
        for m in re.finditer(r"tel:\+?[\d-]+", t):
            if m.group(0) != "tel:+17166018275":
                fails.append(f"NAP: nonstandard tel in {rel}: {m.group(0)}")
        if re.search(r"601[.\s]8275", t) and "(716) 601-8275" not in t:
            fails.append(f"NAP: phone format drift in {rel}")
        if fn != "booking.html" and 'href="booking.html"' in t:
            fails.append(f"stale booking.html href in {rel}")
        for m in re.finditer(r'rel="canonical" href="([^"]+)"', t):
            if not m.group(1).startswith("https://treecareofbuffalo.com/"):
                fails.append(f"canonical not absolute in {rel}: {m.group(1)}")

if fails:
    print("PREDEPLOY: FAIL")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print("PREDEPLOY: PASS (devibe high=0, em dashes=0, NAP locked, canonicals absolute)")
