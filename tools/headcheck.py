# Head-order gate: runs capo.js (rviscomi/capo.js, Apache-2.0, installed by package.json) inside
# headless Edge against every page served from a local http.server, and fails on any ordering
# violation or validation warning. capo's rule: metas and title first, then preconnects, async
# scripts, imported styles, sync scripts, sync styles, preloads, deferred scripts, prefetch; and
# everything else (canonical, Open Graph, JSON-LD, icons, manifest) after the render-critical
# elements, not before them.
#
# Run:  python tools/headcheck.py                 (all pages)
#       python tools/headcheck.py faq.html ...    (named pages)
#       python tools/headcheck.py --browser chromium   (CI, no Edge)
import argparse, functools, http.server, json, os, sys, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "tools", ".gate", ".wrangler", ".netlify", "functions"}
REDIRECT_STUBS = {"booking.html", os.path.join("services", "index.html")}

JS = """async () => {
  const core = await import('/node_modules/@rviscomi/capo.js/src/index.js');
  const ad = await import('/node_modules/@rviscomi/capo.js/src/adapters/index.js');
  const r = core.analyzeHeadWithOrdering(document.head, new ad.BrowserAdapter());
  const snip = e => (e && e.outerHTML) ? e.outerHTML.replace(/\\s+/g, ' ').slice(0, 120) : String(e);
  return {
    violations: (r.orderingViolations || []).map(v => ({index: v.index, message: v.message, current: snip(v.currentElement), next: snip(v.nextElement)})),
    warnings: (r.validationWarnings || []).map(w => ({message: w.message || w.warning || JSON.stringify(w), element: snip(w.element)})),
    custom: (r.customValidations || []).map(w => ({message: w.message || w.warning || JSON.stringify(w), element: snip(w.element)})),
    weights: r.weights.map(w => w.weight)
  };
}"""

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

def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *x, **k): super().__init__(*x, directory=ROOT, **k)
        def log_message(self, *x, **k): pass
        def handle_error(self, *x, **k): pass   # the browser aborts connections; keep socket tracebacks out of the gate output
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--browser", default="msedge", help="msedge (default) or chromium")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
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
    srv = serve(); port = srv.server_address[1]
    results, fails = {}, 0
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel=a.browser) if a.browser != "chromium" else p.chromium.launch()
            pg = b.new_page()
            for rel in pages:
                url = f"http://127.0.0.1:{port}/" + rel.replace(os.sep, "/")
                pg.goto(url, wait_until="domcontentloaded")
                r = pg.evaluate(JS)
                results[rel] = r
                n = len(r["violations"]) + len(r["warnings"]) + len(r["custom"])
                fails += n
                if not a.json:
                    print(f"{'FAIL' if n else 'ok  '} {rel}: {len(r['violations'])} ordering, {len(r['warnings'])} validation, {len(r['custom'])} custom")
                    for v in r["violations"]:
                        print(f"      #{v['index']}: {v['message']}\n         now:  {v['current']}\n         next: {v['next']}")
                    for w in r["warnings"] + r["custom"]:
                        print(f"      warn: {w['message']}  {w['element']}")
            b.close()
    finally:
        srv.shutdown()
    if a.json:
        print(json.dumps(results, indent=1))
    print(f"HEADCHECK: {'FAIL' if fails else 'PASS'} ({len(pages)} pages, {fails} findings)")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
