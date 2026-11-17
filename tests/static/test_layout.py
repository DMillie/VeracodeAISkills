#!/usr/bin/env python3
"""Layout: every skill has valid front matter, entry files stay small, synced folders hold no
orphans, every script parses, no lab-only names or credential-looking strings are in the repository."""
import glob, os, re, subprocess, sys
from _common import *
BUDGET = {"SKILL.md": 14000, "AGENTS.md": 9000}          # bytes an assistant loads before it has decided anything
for s in SKILLS:
    t = open(os.path.join(ROOT, s, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", t, re.S); fm = dict(re.findall(r"(?m)^(\w+):\s*(.*)$", m.group(1))) if m else {}
    check(f"{s}: front matter name equals folder", fm.get("name") == s, str(fm.get("name")))
    d = fm.get("description", ""); check(f"{s}: description present, at most 1024 characters ({len(d)})", 40 <= len(d) <= 1024)
    check(f"{s}: description says when to use it", bool(re.search(r"\b[Uu]se (this |it )?(when|for|whenever)\b", d)), d[:80])
    for f, lim in BUDGET.items():
        p = os.path.join(ROOT, s, f)
        if os.path.isfile(p): n = os.path.getsize(p); check(f"{s}/{f}: {n} bytes, budget {lim}", n <= lim)
# orphans: a file inside a synced folder of a skill that shared/ no longer has
for line in open(os.path.join(ROOT, "shared/manifest.txt")):
    if line.startswith("#") or not line.strip(): continue
    skill, path = line.split(); src = os.path.join(ROOT, "shared", path)
    if os.path.isdir(src):
        have = {os.path.relpath(f, os.path.join(ROOT, skill, path)) for f in glob.glob(os.path.join(ROOT, skill, path, "**/*"), recursive=True) if os.path.isfile(f)}
        want = {os.path.relpath(f, src) for f in glob.glob(os.path.join(src, "**/*"), recursive=True) if os.path.isfile(f)}
        check(f"{skill}/{path}: no orphan copies", have <= want, str(sorted(have - want)[:3]))
tracked = subprocess.check_output(["git", "-C", ROOT, "ls-files", "-co", "--exclude-standard"], text=True).split("\n")
for f in tracked:
    p = os.path.join(ROOT, f)
    if not os.path.isfile(p) or "/fixtures/" in f: continue
    if f.endswith(".py"): r = subprocess.run([sys.executable, "-c", "import ast,sys; ast.parse(open(sys.argv[1]).read())", p], capture_output=True, text=True); check(f"{f}: parses", r.returncode == 0, r.stderr[-120:])
    elif f.endswith(".sh"): r = subprocess.run(["bash", "-n", p], capture_output=True, text=True); check(f"{f}: bash -n", r.returncode == 0, r.stderr[-120:])
    elif f.endswith(".js"): r = subprocess.run(["node", "--check", p], capture_output=True, text=True); check(f"{f}: node --check", r.returncode == 0, r.stderr[-120:])
LEAK = re.compile(r"/home/[a-z]+/|VCDEMO|VCTB-|RUN-00\d|192\.168\.\d+\.\d+|glpat-[\w-]{10,}|\b[0-9a-f]{32}\b(?!.*sha)|BEGIN [A-Z ]*PRIVATE KEY")
bad = []
for f in tracked:
    p = os.path.join(ROOT, f)
    if not os.path.isfile(p) or f.startswith("tests/") or not f.endswith((".md", ".yml", ".py", ".sh", ".js", ".txt", ".json")): continue
    for n, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
        m = LEAK.search(line)
        if m and "sha256" not in line.lower() and "digest" not in line.lower(): bad.append(f"{f}:{n} {m.group(0)[:24]}")
check("no lab-only names, private addresses or secret-looking strings", not bad, "; ".join(bad[:5]))
done()
