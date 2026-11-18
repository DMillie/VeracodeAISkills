#!/usr/bin/env python3
"""Bitbucket draft: structure, pins, no credentials, no double pipelines, honest status line."""
import glob, os, re, subprocess, sys
from _common import *
EX = sorted(glob.glob(os.path.join(PACK, "templates/bitbucket/examples/*.yml")))
check("at least one Bitbucket example", bool(EX))
X = os.path.join(ROOT, "tests/bitbucket/extract_step.py")
for f in EX:
    n = os.path.basename(f); t = open(f).read(); code = "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("#"))
    check(f"{n}: no tab characters, spaces only", "\t" not in t)
    anchors = set(re.findall(r"- step: &([\w-]+)", t)); used = set(re.findall(r"- step: \*([\w-]+)", t))
    check(f"{n}: every step used is defined", used <= anchors, str(used - anchors))
    check(f"{n}: every Veracode step defined is used", {a for a in anchors if a.startswith("veracode")} <= used)
    added = code.split("- step: &veracode-package", 1)[-1].split("\npipelines:")[0]
    imgs = re.findall(r"(?m)^\s+image:\s*(\S+)", added)
    check(f"{n}: every added image pinned tag@sha256", bool(imgs) and all(re.fullmatch(r"[\w/.-]+:[\w.-]*\d[\w.-]*@sha256:[0-9a-f]{64}", i) for i in imgs), str(imgs))
    check(f"{n}: no :latest, no download piped into a shell", not re.search(r":latest\b|LATEST\.zip", added) and not re.search(r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b", added))
    check(f"{n}: credentials only as variable references", not re.search(r"(?i)(-vkey|-vid|api_key\w*\s*[:=])\s*[\"']?[A-Za-z0-9]{16,}", code) and '"$VERACODE_API_KEY_SECRET"' in code)
    check(f"{n}: no `default:` pipeline next to pull-requests (double pipelines)", not re.search(r"(?m)^  default:", code))
    br = re.findall(r"(?m)^  branches:\n((?:    .*\n|      .*\n)+)", code + "\n")
    check(f"{n}: branch pipelines only for named long-lived branches", not br or not re.search(r"(?m)^    ['\"]?\*", br[0]))
    check(f"{n}: audit never fails on findings, fails when nothing was scanned", "modules_count" in t and "did not complete" in t)
    check(f"{n}: policy scan is not waited for", "-scantimeout" not in code)
    check(f"{n}: profile is never created by the pipeline", "-createprofile false" in code)
    check(f"{n}: says it has not run on Bitbucket", "NOT run on Bitbucket" in t)
    for a in sorted(x for x in anchors if x.startswith("veracode")):
        r = subprocess.run([sys.executable, X, f, a, "script"], capture_output=True, text=True)
        s = subprocess.run(["sh", "-n"], input=r.stdout, capture_output=True, text=True)
        check(f"{n}: step {a} script parses as sh", r.returncode == 0 and r.stdout.strip() != "" and s.returncode == 0, (r.stderr + s.stderr)[:200])
facts = open(os.path.join(PACK, "reference/facts/bitbucket.md")).read()
check("facts file says nothing was run on Bitbucket", "Nothing in" in facts and "has been run on Bitbucket" in facts)
done()
