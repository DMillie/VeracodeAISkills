#!/usr/bin/env python3
"""The agent-side scripts give the right verdict on small synthetic result files."""
import json, os, subprocess, sys, tempfile
from _common import *
FX = os.path.join(os.path.dirname(__file__), "fixtures")
def finding(cwe, file, line, sev=3): return {"cwe_id": str(cwe), "severity": sev, "issue_type": "x", "files": {"source_file": {"file": file, "line": line}}}
def write(name, d):
    p = os.path.join(tempfile.gettempdir(), "skilltest-" + name); json.dump(d, open(p, "w")); return p
def scan_check(p, *args):
    r = subprocess.run(["node", os.path.join(PACK, "tools/scan-check.js"), p, *args], capture_output=True, text=True); return r.returncode, r.stdout + r.stderr
good = write("good.json", {"scan_status": "SUCCESS", "modules": ["JS files within app.zip"], "findings": [finding(89, "packages/api/src/db.ts", 14, 4), finding(78, "packages/api/src/run.ts", 9, 5), finding(80, "packages/web/src/view.ts", 30)]})
zero = write("zero.json", {"scan_status": "SUCCESS", "modules": ["JS files within app.zip"], "findings": []})
nomod = write("nomod.json", {"scan_status": "FAILURE", "message": "No files found for scanning", "modules": [], "findings": []})
nodebug = write("nodebug.json", {"scan_status": "SUCCESS", "modules": ["app.dll"], "findings": [finding(89, "UNKNOWN", 1) for _ in range(5)]})
rc, out = scan_check(good); check("scan-check: plausible result passes", rc == 0, out[-200:])
rc, out = scan_check(zero); check("scan-check: SUCCESS with 0 findings is flagged", rc != 0 and "0 findings" in out, out[-200:])
rc, out = scan_check(nomod); check("scan-check: no modules is flagged", rc != 0, out[-200:])
rc, out = scan_check(nodebug); check("scan-check: findings without file or line are flagged", rc != 0 and "debug" in out.lower(), out[-200:])
rc, out = scan_check(good, "--module", "worker.dll"); check("scan-check: a missing expected module is flagged", rc != 0, out[-200:])
rc, out = scan_check(good, "--place", "packages/shared/src/rules.ts"); check("scan-check: a missing expected place is flagged", rc != 0 or "rules.ts" in out, out[-200:])
rc, out = scan_check(good, "--place", "packages/api/src/db.ts"); check("scan-check: a reported expected place passes", rc == 0, out[-200:])
r = subprocess.run([sys.executable, os.path.join(PACK, "tools/pipeline_scan_summary.py"), good], capture_output=True, text=True)
check("pipeline_scan_summary: counts by severity", r.returncode == 0 and "3 findings" in r.stdout and "Very High" in r.stdout, r.stdout[-200:] + r.stderr[-200:])
done()
