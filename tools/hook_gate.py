# Claude Code PostToolUse hook: after any Edit or Write to a shipped .html, .css or .js file in this
# repo, run the quick gate and hand failures back to the session (exit 2 shows stderr to Claude;
# exit 0 stays silent). Wired from .claude/settings.json here and from the parent project's
# .claude/settings.json (sessions usually start there). Reads the hook JSON on stdin.
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = (".html", ".css", ".js")
IGNORE_DIRS = ("tools", "node_modules", ".gate", ".git", ".claude", ".github", "functions")

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    if not path:
        return 0
    path = os.path.abspath(path)
    try:
        rel = os.path.relpath(path, ROOT)
    except ValueError:
        return 0
    if rel.startswith("..") or not path.endswith(SHIPPED) or rel.split(os.sep)[0] in IGNORE_DIRS:
        return 0
    cmd = [sys.executable, os.path.join(ROOT, "tools", "gate.py"), "--quick"]
    if path.endswith(".html"):
        cmd.append(path)
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(f"GATE FAILED after editing {rel}. Fix before moving on.\n")
        sys.stderr.write((r.stdout or "")[-6000:] + (r.stderr or "")[-2000:])
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
