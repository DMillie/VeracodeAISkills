"""Shared helpers for the tests (standard library only). PACK is the skill that carries the full file set."""
import glob, json, os, sys, urllib.error, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACK = os.environ.get("PACK") or os.path.join(ROOT, "veracode-repo-onboarding")
URL = os.environ.get("GITLAB_URL", "")
TOKEN = os.environ.get("GITLAB_TOKEN", "")
LINT_PROJECT = os.environ.get("LINT_PROJECT", "")
COMPONENT_PROJECT = os.environ.get("COMPONENT_PROJECT", "platform/veracode-ci")
TEMPLATE = os.path.join(PACK, "templates/gitlab/component/templates/veracode/template.yml")
EXAMPLES = sorted(glob.glob(os.path.join(PACK, "templates/gitlab/examples/*.yml")))
SKILLS = sorted(d for d in os.listdir(ROOT) if os.path.isfile(os.path.join(ROOT, d, "SKILL.md")))
results = []
def check(name, ok, detail=""):
    results.append(bool(ok)); print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  [{detail}]" if detail and not ok else ""))
def done():
    print(f"  {sum(results)}/{len(results)} checks passed"); sys.exit(0 if all(results) else 1)
def skip(why):
    print(f"  SKIPPED: {why}"); sys.exit(0)
def api(method, path, body=None):
    req = urllib.request.Request(f"{URL}/api/v4{path}", method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("PRIVATE-TOKEN", TOKEN); req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read()[:300].decode(errors="replace")}
def lint(content, project=None, ref=None):
    body = {"content": content, "include_jobs": True}
    if ref: body.update(ref=ref, dry_run=True)
    st, out = api("POST", f"/projects/{urllib.parse.quote(project or LINT_PROJECT, safe='')}/ci/lint", body)
    return out if st in (200, 201) else {"valid": False, "errors": [f"HTTP {st} {out}"], "warnings": [], "jobs": []}
def component_version():
    import re
    return re.search(r'VERACODE_COMPONENT_VERSION: "([^"]+)"', open(TEMPLATE).read()).group(1)
