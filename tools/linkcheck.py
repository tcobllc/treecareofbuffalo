# Link gate. Offline by default: every internal href, src, srcset, poster, inline-style url(),
# canonical and Open Graph image, and every anchor (same-page or cross-page) in every HTML, CSS
# and webmanifest file must resolve to a file in this repo with the exact on-disk spelling
# (Windows is case-insensitive, the hosts are not). Directories resolve to index.html,
# extensionless pages to <name>.html, absolute self-links on treecareofbuffalo.com are checked as
# internal, and the _redirects file is honored for its source paths. With --external it also runs
# linkinator (installed by package.json) against a local server and follows outbound links.
#
# Run:  python tools/linkcheck.py            python tools/linkcheck.py --external
import argparse, http.server, json, os, re, shutil, subprocess, sys, threading

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace"); sys.stderr.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "tools", ".gate", ".wrangler", ".netlify"}
SELF = re.compile(r'^https?://(www\.)?treecareofbuffalo\.com(/|$)', re.I)
ATTR = re.compile(r'\b(?:href|src|poster|data-src)="([^"]+)"')
META_URL = re.compile(r'<(?:meta|link)\b[^>]*\b(?:property|name|rel)="(?:og:image|twitter:image|og:url|canonical|icon|apple-touch-icon|manifest)"[^>]*\b(?:content|href)="([^"]+)"')
SRCSET = re.compile(r'\bsrcset="([^"]+)"')
STYLE_BLOCK = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S | re.I)
IDS = re.compile(r'\bid="([^"]+)"')
CSS_URL = re.compile(r'url\((["\']?)([^)"\']+)\1\)')

def files():
    for dp, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in fs:
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

def exact_case(path):
    """True when every component of path exists with exactly this spelling (Windows is case-insensitive)."""
    rel = os.path.relpath(path, ROOT)
    cur = ROOT
    for part in rel.split(os.sep):
        if part not in os.listdir(cur):
            return False
        cur = os.path.join(cur, part)
    return True

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

_ids_cache = {}
def ids_in(path):
    if path not in _ids_cache:
        try:
            _ids_cache[path] = set(IDS.findall(open(path, encoding="utf-8").read()))
        except OSError:
            _ids_cache[path] = set()
    return _ids_cache[path]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true")
    a = ap.parse_args()
    red = redirects()
    fails = []
    for f in files():
        text = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, ROOT)
        targets = []
        if f.endswith(".html"):
            targets += ATTR.findall(text) + META_URL.findall(text)
            for ss in SRCSET.findall(text):
                targets += [part.strip().split()[0] for part in ss.split(",") if part.strip()]
            for block in STYLE_BLOCK.findall(text):
                targets += [m[1] for m in CSS_URL.findall(block) if not m[1].startswith("data:")]
        elif f.endswith(".css"):
            targets = [m[1] for m in CSS_URL.findall(text) if not m[1].startswith("data:")]
        else:  # webmanifest
            try:
                targets = [i.get("src", "") for i in json.loads(text).get("icons", [])]
            except ValueError:
                fails.append(f"{rel}: not valid JSON")
        for t in targets:
            if SELF.match(t):
                t = "/" + re.sub(SELF, "", t)          # absolute self-link: check as internal
            if re.match(r'^(https?:|mailto:|tel:|sms:|data:|javascript:|//)', t):
                continue
            if t.startswith("#"):
                if t != "#" and t[1:] not in IDS.findall(text):
                    fails.append(f"{rel}: missing anchor {t}")
                continue
            if t.split("#")[0] in red:
                continue
            path = resolve(f, t)
            if path is None:
                continue
            if not os.path.exists(path):
                fails.append(f"{rel}: broken {t} -> {os.path.relpath(path, ROOT)}")
                continue
            if not exact_case(path):
                fails.append(f"{rel}: case mismatch {t} (on disk: {os.path.relpath(path, ROOT)})")
            if "#" in t and path.endswith(".html"):
                frag = t.split("#", 1)[1]
                if frag and frag not in ids_in(path):
                    fails.append(f"{rel}: missing anchor #{frag} in {os.path.relpath(path, ROOT)}")
    if a.external:
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *x, **k): super().__init__(*x, directory=ROOT, **k)
            def log_message(self, *x, **k): pass
            def handle_error(self, *x, **k): pass
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        port = srv.server_address[1]
        node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
        lk = os.path.join(ROOT, "node_modules", "linkinator", "build", "src", "cli.js")
        r = subprocess.run([node, lk, f"http://127.0.0.1:{port}/", "--recurse", "--timeout", "15000", "--format", "json",
                            "--skip", "challenges.cloudflare.com", "--skip", "treecareofbuffalo.com", "--skip", "pages.dev"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "FORCE_COLOR": "0"})
        srv.shutdown()
        broken = []
        try:
            data = json.loads(r.stdout)
            broken = [l for l in data.get("links", []) if l.get("state") == "BROKEN"]
            for l in broken:
                fails.append(f"external: [{l.get('status')}] {l.get('url')} (on {l.get('parent')})")
            print(f"linkinator: {len(data.get('links', []))} links, {len(broken)} broken, exit {r.returncode}")
        except ValueError:
            fails.append(f"external: linkinator produced no JSON (exit {r.returncode}): {(r.stderr or r.stdout)[-600:]}")
        if r.returncode != 0 and not broken and not any(x.startswith("external:") for x in fails):
            fails.append(f"external: linkinator exit {r.returncode}: {(r.stderr or '')[-600:]}")
    for x in fails:
        print(" -", x)
    print(f"LINKCHECK: {'FAIL' if fails else 'PASS'} ({len(fails)} broken)")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
