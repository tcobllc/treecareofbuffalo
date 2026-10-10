# Email swap for the lead paths. The site shows business@treecareofbuffalo.com everywhere, but the
# two places that actually deliver mail still point at the owner's Gmail from before Workspace
# existed: the mailto fallbacks in assets/site.js (estimate form and quick-contact popup) and the
# Resend recipient in functions/api/lead.js.
#
#   python tools/swap_email.py --mailto business@treecareofbuffalo.com
#       rewrites the two mailto targets (safe as soon as the mailbox receives mail)
#   python tools/swap_email.py --dest business@treecareofbuffalo.com --from leads@treecareofbuffalo.com
#       rewrites DEST and FROM in lead.js. Only after the domain is verified in Resend: the
#       unverified tier delivers to the Resend account owner's address only, so flipping DEST
#       early silently drops every form lead.
#   python tools/swap_email.py --show        prints the current values and exits
import argparse, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_JS = os.path.join(ROOT, "assets", "site.js")
LEAD_JS = os.path.join(ROOT, "functions", "api", "lead.js")

def rd(p): return io.open(p, encoding="utf-8", newline="").read()
def wr(p, t): io.open(p, "w", encoding="utf-8", newline="").write(t)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mailto", help="new address for the mailto fallbacks in site.js")
    ap.add_argument("--dest", help="new DEST (recipient) in lead.js")
    ap.add_argument("--from", dest="from_", help="new FROM (sender) in lead.js")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    js, lead = rd(SITE_JS), rd(LEAD_JS)
    cur_mailto = sorted(set(re.findall(r"mailto:([^?'\"]+)", js)))
    cur_dest = re.search(r'const DEST = "([^"]+)"', lead).group(1)
    cur_from = re.search(r'const FROM = "([^"]+)"', lead).group(1)
    print(f"site.js mailto targets: {cur_mailto}\nlead.js DEST: {cur_dest}\nlead.js FROM: {cur_from}")
    if a.show or not (a.mailto or a.dest or a.from_):
        return 0
    if a.mailto:
        n = 0
        for old in cur_mailto:
            js, k = re.subn(r"mailto:" + re.escape(old), "mailto:" + a.mailto, js); n += k
        wr(SITE_JS, js); print(f"site.js: {n} mailto targets -> {a.mailto}")
    if a.dest or a.from_:
        if a.dest:
            lead = lead.replace(f'const DEST = "{cur_dest}"', f'const DEST = "{a.dest}"')
        if a.from_:
            lead = lead.replace(f'const FROM = "{cur_from}"', f'const FROM = "{a.from_}"')
        wr(LEAD_JS, lead); print(f"lead.js: DEST -> {a.dest or cur_dest}, FROM -> {a.from_ or cur_from}")
    print("Now run: python tools/gate.py  and redeploy the preview; the Function change only takes effect on deploy.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
