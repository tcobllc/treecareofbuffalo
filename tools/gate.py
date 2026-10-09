# The deterministic gate. One command, every check, nonzero exit on any failure.
#
#   python tools/gate.py                   full: predeploy, html-validate, head order, links, axe
#   python tools/gate.py --quick FILE...   hook mode: predeploy + html-validate + head order + links,
#                                          scoped to the named HTML files where a check supports it
#   python tools/gate.py --external        also follow outbound links (network)
#   python tools/gate.py --browser chromium   CI (no Edge)
#
# Each step is its own script in tools/ and can be run alone. Needs: Python 3.10+ with playwright
# and axe-playwright-python, Node 22+ with `npm install` done once (package.json pins the versions).
import argparse, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
# Call the JS entry points through node, not the .cmd shims: cmd.exe splits this repo's path on the
# comma in "TCOB,LLC", and Node is not on PATH in every shell on this machine.
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
HTML_VALIDATE = os.path.join(ROOT, "node_modules", "html-validate", "bin", "html-validate.mjs")

def run(label, cmd, cwd=ROOT):
    t = time.time()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    ok = r.returncode == 0
    print(f"[{'PASS' if ok else 'FAIL'}] {label} ({time.time() - t:.1f}s)")
    if not ok:
        print("      " + "\n      ".join(out.strip().splitlines()[-40:]))
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="HTML files to scope html-validate and head order to")
    ap.add_argument("--quick", action="store_true", help="skip axe (hook mode)")
    ap.add_argument("--external", action="store_true")
    ap.add_argument("--browser", default="msedge")
    a = ap.parse_args()
    html = [f for f in a.files if f.endswith(".html")]
    if not os.path.isdir(os.path.join(ROOT, "node_modules")):
        print("node_modules missing: run `npm install` in the site folder once"); sys.exit(2)
    results = []
    results.append(run("predeploy.py (devibe, em dashes, NAP, canonicals, SEO floors, sitemap)", [PY, os.path.join(ROOT, "tools", "predeploy.py")]))
    results.append(run("html-validate (recommended + a11y presets, .htmlvalidate.json)", [NODE, HTML_VALIDATE] + (html or ["**/*.html"])))
    results.append(run("head order (capo.js)", [PY, os.path.join(ROOT, "tools", "headcheck.py"), "--browser", a.browser] + html))
    results.append(run("links (internal" + (", external" if a.external else "") + ")", [PY, os.path.join(ROOT, "tools", "linkcheck.py")] + (["--external"] if a.external else [])))
    if not a.quick:
        results.append(run("axe-core accessibility (all pages)", [PY, os.path.join(ROOT, "tools", "a11y.py"), "--browser", a.browser]))
    bad = results.count(False)
    print(f"GATE: {'FAIL' if bad else 'PASS'} ({len(results) - bad}/{len(results)} checks)")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
