# Accessibility gate: axe-core (Deque, MPL-2.0) through axe-playwright-python, every page, headless
# Edge by default (chromium in CI). Lighthouse's accessibility score samples a subset of axe rules;
# this runs the full default ruleset. Critical and serious violations fail the gate; moderate and
# minor are printed as warnings. The Turnstile iframe is excluded (third-party, needs network).
#
# Run:  python tools/a11y.py            python tools/a11y.py estimate/index.html --browser chromium
import argparse, functools, http.server, json, os, sys, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "tools", ".gate", ".wrangler", ".netlify", "functions"}
REDIRECT_STUBS = {"booking.html", os.path.join("services", "index.html")}

def all_pages():
    out = []
    for dp, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".html"):
                rel = os.path.relpath(os.path.join(dp, f), ROOT)
                if rel not in REDIRECT_STUBS:
                    out.append(rel)
    return sorted(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--browser", default="msedge")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    from axe_playwright_python.sync_playwright import Axe
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pages = []
    for p in a.pages:
        try:
            rel = os.path.relpath(os.path.abspath(p), ROOT)
        except ValueError:
            rel = ".."
        if rel.startswith(".."):
            print(f"not inside the repo, skipped: {p}"); continue
        pages.append(rel)
    pages = pages or all_pages()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *x, **k): super().__init__(*x, directory=ROOT, **k)
        def log_message(self, *x, **k): pass
        def handle_error(self, *x, **k): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    axe = Axe()
    report, fails, warns = {}, 0, 0
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel=a.browser) if a.browser != "chromium" else p.chromium.launch()
            ctx = b.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            pg = ctx.new_page()
            for rel in pages:
                pg.goto(f"http://127.0.0.1:{port}/" + rel.replace(os.sep, "/"), wait_until="load")
                pg.wait_for_timeout(300)
                res = axe.run(pg, context={"exclude": [["iframe"]]}).response
                vio = res.get("violations", [])
                bad = [v for v in vio if v.get("impact") in ("critical", "serious")]
                soft = [v for v in vio if v.get("impact") not in ("critical", "serious")]
                fails += len(bad); warns += len(soft)
                report[rel] = vio
                if not a.json:
                    print(f"{'FAIL' if bad else 'ok  '} {rel}: {len(bad)} serious+, {len(soft)} minor, {len(res.get('passes', []))} rules passed")
                    for v in bad + soft:
                        tgt = "; ".join(n["target"][0] if isinstance(n["target"], list) and n["target"] else str(n["target"]) for n in v["nodes"][:3])
                        print(f"      [{v['impact']}] {v['id']}: {v['help']}  ->  {tgt}")
            b.close()
    finally:
        srv.shutdown()
    if a.json:
        print(json.dumps(report, indent=1))
    print(f"A11Y: {'FAIL' if fails else 'PASS'} ({len(pages)} pages, {fails} serious or critical, {warns} moderate or minor)")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
