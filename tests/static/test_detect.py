#!/usr/bin/env python3
"""Idempotency logic (tools/detect_integration.py): an onboarded file is recognised, the upgrade is
a one-line diff, nothing is proposed twice."""
import json, os, subprocess, sys, tempfile
from _common import *
TOOL = os.path.join(PACK, "tools/detect_integration.py")
def run(text, *args):
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f: f.write(text)
    env = {k: v for k, v in os.environ.items() if k not in ("GITLAB_URL", "GITLAB_TOKEN")}
    out = json.loads(subprocess.check_output([sys.executable, TOOL, f.name, *args], text=True, env=env)); os.unlink(f.name); return out
ex = open(EXAMPLES[0]).read(); ver = component_version()
o = run(ex, "--latest", ver); check(f"example at {ver}, latest {ver}: nothing to do", o["mode"] == "component" and o["version"] == ver and o["action"] == "nothing" and not o["diff"], str(o))
o = run(ex, "--latest", "9.9.9"); d = [l for l in o["diff"].splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---")]
check("newer release: action upgrade", o["action"] == "upgrade", str(o))
check("upgrade diff is exactly one line changed (1 removed, 1 added)", len(d) == 2 and d[0].startswith("-") and d[1].startswith("+") and "@9.9.9" in d[1], str(d))
o = run(ex.replace("@" + ver, "@main"), "--latest", ver); check("branch ref: action pin", o["action"] == "pin", str(o))
o = run("include:\n  - project: platform/veracode-ci\n    ref: 1.0.0\n    file: templates/veracode/template.yml\n", "--latest", "1.1.0"); check("project include: upgrade", o["mode"] == "project-include" and o["action"] == "upgrade" and "+    ref: 1.1.0" in o["diff"], str(o))
o = run("include:\n  - local: .gitlab/veracode.yml\nx:\n  extends: .veracode-pipeline-scan\n"); check("legacy copy: migrate", o["mode"] == "legacy-copy" and o["action"] == "migrate", str(o))
o = run("include:\n  - local: .gitlab/veracode/template.yml\n"); check("local copy: migrate", o["mode"] == "local-copy", str(o))
o = run("scan:\n  script: java -jar pipeline-scan.jar\n"); check("hand-written Veracode job: review, not a second integration", o["action"] == "review", str(o))
o = run("build:\n  script: make\n"); check("no integration: onboard", o["action"] == "onboard", str(o))
done()
