# Reorders every <head> into capo.js order, using capo's own weights (asked from the library in a
# headless browser, so the categories match tools/headcheck.py exactly). The sort is stable: elements
# keep their relative order inside a group, and the file's text for each element is moved verbatim
# (no re-serialization, so attribute quoting, JSON-LD blocks and the inline <style> survive intact).
# Pages whose parsed element count disagrees with the DOM are skipped with a warning.
#
# Run:  python tools/fix_head_order.py            (rewrites files in place; run headcheck after)
#       python tools/fix_head_order.py --dry-run
import argparse, functools, http.server, os, re, sys, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "tools", ".gate", ".wrangler", ".netlify", "functions"}
REDIRECT_STUBS = {"booking.html", os.path.join("services", "index.html")}
EL = re.compile(r'<!--.*?-->|<(?:meta|link|base)\b[^>]*>|<title\b[^>]*>.*?</title>|<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<noscript\b[^>]*>.*?</noscript>', re.S | re.I)
JS = """async () => {
  const rules = await import('/node_modules/@rviscomi/capo.js/src/lib/rules.js');
  const ad = await import('/node_modules/@rviscomi/capo.js/src/adapters/index.js');
  const a = new ad.BrowserAdapter();
  return rules.getHeadWeights(document.head, a).map(w => w.weight);
}"""

def pages():
    for dp, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith(".html"):
                rel = os.path.relpath(os.path.join(dp, f), ROOT)
                if rel not in REDIRECT_STUBS:   # meta-refresh stubs navigate away before capo can run
                    yield rel

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--browser", default="msedge")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *x, **k): super().__init__(*x, directory=ROOT, **k)
        def log_message(self, *x, **k): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    changed = 0
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel=a.browser) if a.browser != "chromium" else p.chromium.launch()
            pg = b.new_page()
            for rel in pages():
                path = os.path.join(ROOT, rel)
                text = open(path, encoding="utf-8", newline="").read()
                m = re.search(r'(<head\b[^>]*>)(.*?)(</head>)', text, re.S | re.I)
                if not m:
                    continue
                inner = m.group(2)
                tokens = [t for t in EL.finditer(inner)]
                elements = [t for t in tokens if not t.group(0).startswith("<!--")]
                pg.goto(f"http://127.0.0.1:{port}/" + rel.replace(os.sep, "/"), wait_until="domcontentloaded")
                weights = pg.evaluate(JS)
                if len(weights) != len(elements):
                    print(f"skip {rel}: parsed {len(elements)} elements, DOM has {len(weights)}")
                    continue
                order = sorted(range(len(elements)), key=lambda i: -weights[i])   # stable
                if order == list(range(len(elements))):
                    print(f"ok   {rel}")
                    continue
                # rebuild: keep the leading whitespace of each original slot, drop comments between elements
                slots = []
                pos = 0
                for t in elements:
                    slots.append(inner[pos:t.start()])
                    pos = t.end()
                tail = inner[pos:]
                lead = [re.sub(r'<!--.*?-->', '', s, flags=re.S) for s in slots]
                new_inner = "".join(lead[i] + elements[order[i]].group(0) for i in range(len(elements))) + tail
                new_text = text[:m.start(2)] + new_inner + text[m.end(2):]
                print(f"FIX  {rel}: moved {sum(1 for i, j in enumerate(order) if i != j)} of {len(elements)} head elements")
                changed += 1
                if not a.dry_run:
                    open(path, "w", encoding="utf-8", newline="").write(new_text)
            b.close()
    finally:
        srv.shutdown()
    print(f"fix_head_order: {changed} pages {'would change' if a.dry_run else 'rewritten'}")

if __name__ == "__main__":
    main()
