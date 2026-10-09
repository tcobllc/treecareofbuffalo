# Link gate. Offline by default: every internal href, src, srcset, poster and same-page anchor in
# every HTML file must resolve to a file in this repo (directories resolve to index.html; the
# _redirects file is honored for its source paths). With --external it also runs linkinator
# (installed by package.json) against a local server and follows outbound links.
#
# Run:  python tools/linkcheck.py            python tools/linkcheck.py --external
import argparse, functools, http.server, os, re, subprocess, sys, threading, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "tools", ".gate", ".wrangler", ".netlify"}
ATTR = re.compile(r'\b(?:href|src|poster|data-src)="([^"]+)"')
SRCSET = re.compile(r'\bsrcset="([^"]+)"')
IDS = re.compile(r'\bid="([^"]+)"')
CSS_URL = re.compile(r'url\((["\']?)([^)"\']+)\1\)')

def pages():
    for dp, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".html", ".css", ".webmanifest")):
                yield os.path.join(dp, f)

def redirects():
    p = os.path.join(ROOT, "_redirects")
    out = set()
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            parts = line.split()
            if parts and not parts[0].startswith("#"):
                out.add(parts[0])
    return out

def resolve(base_file, target):
    t = target.split("#", 1)[0].split("?", 1)[0]
    if not t:
        return None
    if t.startswith("/"):
        path = os.path.join(ROOT, t.lstrip("/").replace("/", os.sep))
    else:
        path = os.path.normpath(os.path.join(os.path.dirname(base_file), t.replace("/", os.sep)))
    if os.path.isdir(path):
        path = os.path.join(path, "index.html")
    elif not os.path.exists(path) and not os.path.splitext(path)[1] and os.path.exists(path + ".html"):
        path = path + ".html"   # Cloudflare Pages and GitHub Pages both serve /why-us from why-us.html
    return path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true")
    a = ap.parse_args()
    red = redirects()
    fails = []
    for f in pages():
        text = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, ROOT)
        ids = set(IDS.findall(text))
        targets = ATTR.findall(text)
        for ss in SRCSET.findall(text):
            targets += [part.strip().split()[0] for part in ss.split(",") if part.strip()]
        if f.endswith(".css"):
            targets = [m[1] for m in CSS_URL.findall(text) if not m[1].startswith("data:")]
        for t in targets:
            if re.match(r'^(https?:|mailto:|tel:|sms:|data:|javascript:|//)', t):
                continue
            if t.startswith("#"):
                if t != "#" and t[1:] not in ids:
                    fails.append(f"{rel}: missing anchor {t}")
                continue
            if t.split("#")[0] in red:
                continue
            path = resolve(f, t)
            if path and not os.path.exists(path):
                fails.append(f"{rel}: broken {t} -> {os.path.relpath(path, ROOT)}")
    if a.external:
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *x, **k): super().__init__(*x, directory=ROOT, **k)
            def log_message(self, *x, **k): pass
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_address[1]
        import shutil
        node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
        lk = os.path.join(ROOT, "node_modules", "linkinator", "build", "src", "cli.js")
        r = subprocess.run([node, lk, f"http://127.0.0.1:{port}/", "--recurse", "--timeout", "15000",
                            "--skip", "challenges.cloudflare.com", "--skip", "treecareofbuffalo.com",
                            "--skip", "pages.dev"], capture_output=True, text=True)
        srv.shutdown()
        bad = [l for l in r.stdout.splitlines() if "[" in l and "] " in l and not l.strip().startswith("[200]")]
        for l in bad:
            if "[4" in l or "[5" in l or "[0]" in l:
                fails.append("external: " + l.strip())
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-400:])
    for x in fails:
        print(" -", x)
    print(f"LINKCHECK: {'FAIL' if fails else 'PASS'} ({len(fails)} broken)")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
