#!/usr/bin/env python3
"""Keep the copies of shared files inside each skill identical to shared/.

  python3 tools/sync_shared.py sync    copy shared/ into the skills listed in shared/manifest.txt
  python3 tools/sync_shared.py check   exit 1 if a copy differs, or if a skill's Markdown
                                       points at a file that is not in that skill

Skills are installed one folder at a time, so each must carry its own copy. Edit shared/, never
the copies.
"""
import filecmp, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
PATH_RE = re.compile(r"`((?:playbook|reference|templates|tools)/[A-Za-z0-9_./-]+)`(?! \(in the )")
COMPONENT = "templates/gitlab/component"  # paths inside the component project are relative to it


def ignored(skill):
    """Lines `<skill> !<path>` name a path the skill's neutral files mention but the skill deliberately lacks."""
    return {l.split()[1][1:] for l in (SHARED / "manifest.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#") and l.split()[0] == skill and l.split()[1].startswith("!")}


def entries():
    for line in (SHARED / "manifest.txt").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            skill, rel = line.split()
            if rel.startswith("!"):
                continue
            src = SHARED / rel
            files = [p for p in src.rglob("*") if p.is_file()] if src.is_dir() else [src]
            for f in files:
                yield skill, f, ROOT / skill / f.relative_to(SHARED)


def sync():
    n = 0
    for _, src, dst in entries():
        if not src.exists():
            print(f"missing in shared/: {src.relative_to(SHARED)} (not copied)")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            shutil.copy2(src, dst)
            n += 1
    print(f"synced: {n} file(s) updated")


def check():
    bad = []
    for skill, src, dst in entries():
        if not dst.exists():
            bad.append(f"missing copy: {dst.relative_to(ROOT)}")
        elif not filecmp.cmp(src, dst, shallow=False):
            bad.append(f"differs from shared/: {dst.relative_to(ROOT)}")
    for skill_md in ROOT.glob("*/SKILL.md"):
        skill = skill_md.parent
        for md in skill.rglob("*.md"):
            for ref in PATH_RE.findall(md.read_text()):
                ref = ref.rstrip(".")
                if "<" in ref or "*" in ref or ref in ignored(skill.name):
                    continue
                if not (skill / ref).exists() and not (skill / COMPONENT / ref).exists():
                    bad.append(f"dead path in {md.relative_to(ROOT)}: {ref}")
    for b in sorted(set(bad)):
        print(b)
    print("check: OK" if not bad else f"check: {len(set(bad))} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "sync":
        sync()
    elif cmd == "check":
        sys.exit(check())
    else:
        sys.exit(__doc__)
