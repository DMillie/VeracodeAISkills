#!/usr/bin/env python3
"""Detect an existing Veracode integration in a GitLab CI file and say what a re-run should do.

  usage: detect_integration.py CI_FILE [--latest X.Y.Z] [--component-project platform/veracode-ci] [--write]
Prints one JSON object:
  mode     component | project-include | local-copy | legacy-copy | foreign | none
  version  the pinned version/ref found (component and project-include modes)
  latest   newest released semantic version of the component project (from --latest, or read from the
           GitLab tags API with GITLAB_URL + GITLAB_TOKEN; null if neither is available)
  action   nothing | upgrade | pin | migrate | review | onboard
  detail   one sentence for the plan
  diff     unified diff of the proposed change (upgrade/pin only: a one-line version bump)
--write applies that diff to CI_FILE. Never adds jobs: adding the integration is the onboarding
change itself (playbook/05); this tool only prevents doing it twice. Standard library only.
"""
import argparse, difflib, json, os, re, sys, urllib.parse, urllib.request

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
def vkey(v): return tuple(int(x) for x in v.split("."))

def latest_from_gitlab(project):
    url, tok = os.environ.get("GITLAB_URL"), os.environ.get("GITLAB_TOKEN")
    if not (url and tok): return None
    req = urllib.request.Request(f"{url}/api/v4/projects/{urllib.parse.quote(project, safe='')}/repository/tags?per_page=100")
    req.add_header("PRIVATE-TOKEN", tok)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: tags = [t["name"] for t in json.loads(r.read())]
    except Exception: return None
    tags = [t for t in tags if SEMVER.match(t)]
    return max(tags, key=vkey) if tags else None

def detect(text, project):
    code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    name = re.escape(project)
    m = re.search(rf"(?m)^(\s*-?\s*component:\s*\S*/{name}/[\w-]+@)(\S+)\s*$", code)
    if m: return "component", m.group(2), m
    m = re.search(rf"(?ms)project:\s*['\"]?{name}['\"]?\s*\n(?:\s+(?!-).*\n)*?\s*ref:\s*['\"]?([^\s'\"]+)", code)
    if m: return "project-include", m.group(1), m
    if re.search(r"local:\s*['\"]?/?\.gitlab/veracode/template\.yml", code): return "local-copy", None, None
    if re.search(r"local:\s*['\"]?/?\.gitlab/veracode\.yml", code) or re.search(r"extends:\s*\.veracode-", code): return "legacy-copy", None, None
    if re.search(r"(?i)veracode|srcclr|pipeline-scan\.jar", code): return "foreign", None, None
    return "none", None, None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ci_file"); ap.add_argument("--latest")
    ap.add_argument("--component-project", default="platform/veracode-ci"); ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    text = open(a.ci_file).read() if os.path.exists(a.ci_file) else ""
    mode, version, _ = detect(text, a.component_project)
    latest = a.latest or latest_from_gitlab(a.component_project)
    out = {"mode": mode, "version": version, "latest": latest, "action": None, "detail": "", "diff": ""}
    new = None
    if mode in ("component", "project-include"):
        if not SEMVER.match(version or ""):
            out["action"] = "pin"; out["detail"] = f"Included at '{version}', which is not an exact release; pin to {latest or 'the newest release'}."
        elif latest is None:
            out["action"] = "nothing"; out["detail"] = f"Already onboarded ({mode} at {version}); newest release unknown (no --latest, no GitLab access)."
        elif vkey(version) < vkey(latest):
            out["action"] = "upgrade"; out["detail"] = f"Already onboarded ({mode} at {version}); release {latest} exists: propose a one-line version bump."
        else:
            out["action"] = "nothing"; out["detail"] = f"Already onboarded ({mode} at {version}, the newest release). Nothing to do."
        if out["action"] in ("upgrade", "pin") and latest:
            pat = (rf"(?m)^(\s*-?\s*component:\s*\S*/{re.escape(a.component_project)}/[\w-]+@)\S+" if mode == "component"
                   else rf"(?m)^(\s*ref:\s*['\"]?){re.escape(version)}")
            new = re.sub(pat, lambda m: m.group(1) + latest, text, count=1)
            out["diff"] = "".join(difflib.unified_diff(text.splitlines(True), new.splitlines(True), "a/" + os.path.basename(a.ci_file), "b/" + os.path.basename(a.ci_file), n=1))
    elif mode == "local-copy":
        out["action"] = "migrate"; out["detail"] = "Per-repo copy of the component (last-resort rung). If the shared component is readable now, replace the local include by the component include and delete the copy; otherwise refresh the copy from the newest release."
    elif mode == "legacy-copy":
        out["action"] = "migrate"; out["detail"] = "2026-11-11 pack layout (.gitlab/veracode.yml hidden jobs + extends). Replace by the component include; remove the copied file and the extending jobs in one MR."
    elif mode == "foreign":
        out["action"] = "review"; out["detail"] = "Veracode scanning exists but not through the organisation component. Do not add a second integration; report what is there and ask."
    else:
        out["action"] = "onboard"; out["detail"] = "No Veracode integration found."
    if a.write and new and new != text:
        open(a.ci_file, "w").write(new); out["written"] = True
    print(json.dumps(out, indent=1))

if __name__ == "__main__": main()
