#!/usr/bin/env python3
"""Azure DevOps helper for onboarding one repository to Veracode. Standard library only.

Credentials come from the environment and are never printed: AZURE_DEVOPS_ORG (name or https://dev.azure.com/<name>)
and AZURE_DEVOPS_PAT. Global options before or after the subcommand: --project (default veracode-demo), --json.

  ado.py discover <repo>                      everything to know before changing a repository (read only)
  ado.py clone <repo> <dir>                   git clone, token in an http.extraheader only (never stored)
  ado.py push <dir> <branch>                  push HEAD of <dir> to <branch>; the branch must start with veracode/; never forces
  ado.py validate <repo> <pipeline> <branch> [--file local.yml]
                                              pipeline preview API (the lint): OK + step names, or the error
  ado.py detect <dir>                         already onboarded? prints: nothing to do | upgrade | not onboarded
  ado.py pr-create <repo> <source> <target> --title T --description-file F
  ado.py pr-status <repo> <id>
  ado.py pr-complete <repo> <id> [--strategy noFastForward|squash|rebase|rebaseMerge]
                                              refuses unless the latest run of the source branch, on the PR's source
                                              commit, ended succeeded or partiallySucceeded
  ado.py run <repo> <pipeline> <branch>       queue a run
  ado.py runs <repo> [--branch B] [--top N]   recent runs
  ado.py run-wait <id> [--timeout S]          poll until done; stage/job/step results and warnings; exit 1 unless (partially) succeeded
  ado.py run-log <id> [--step TEXT]           log of the steps whose name contains TEXT (default: steps with issues or failures)
  ado.py artifact <id> <name> <dir>           download a pipeline artifact and unzip it into <dir>
  ado.py profile <name> [--create]            Veracode application profile by exact name (get; --create = get or create)
"""
import argparse, base64, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_REPO = "veracode-pipelines"
STRATEGIES = {"noFastForward", "squash", "rebase", "rebaseMerge"}


# ---------------------------------------------------------------- plumbing
def die(msg, code=2):
    print("ERROR: " + msg, file=sys.stderr); sys.exit(code)

def creds():
    org, pat = os.environ.get("AZURE_DEVOPS_ORG", ""), os.environ.get("AZURE_DEVOPS_PAT", "")
    if not org or not pat: die("AZURE_DEVOPS_ORG and AZURE_DEVOPS_PAT must be set in the environment")
    return org.rstrip("/").split("/")[-1], pat

class Az:
    def __init__(self, project):
        self.org, pat = creds(); self.project = project
        self.auth = base64.b64encode((":" + pat).encode()).decode()
        self.base = f"https://dev.azure.com/{self.org}"
    def call(self, method, path, body=None, raw=False, project=True):
        url = path if path.startswith("http") else self.base + ("/" + urllib.parse.quote(self.project) if project else "") + path
        if "api-version" not in url and not raw: url += ("&" if "?" in url else "?") + "api-version=7.1"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={"Authorization": "Basic " + self.auth})
        if data is not None: req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                b = r.read()
        except urllib.error.HTTPError as e:
            b = e.read()
            try: msg = json.loads(b).get("message") or b[:300].decode(errors="replace")
            except Exception: msg = b[:300].decode(errors="replace")
            die(f"{method} {re.sub(r'https://dev.azure.com/[^/]+', '', url.split('?')[0])} -> HTTP {e.code}: {str(msg)[:600]}", 1)
        except urllib.error.URLError as e:
            die(f"network error: {e.reason}", 1)
        if raw: return b
        return json.loads(b) if b[:1] in (b"{", b"[") else {"_raw": b.decode(errors="replace")}
    def get(self, path, **kw): return self.call("GET", path, **kw)
    def repo(self, name):
        return self.get(f"/_apis/git/repositories/{urllib.parse.quote(name)}")
    def git_env(self):
        e = dict(os.environ)
        e.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.extraheader",
                  "GIT_CONFIG_VALUE_0": "Authorization: Basic " + self.auth, "GIT_TERMINAL_PROMPT": "0"})
        return e
    def remote(self, repo):
        return f"{self.base}/{urllib.parse.quote(self.project)}/_git/{urllib.parse.quote(repo)}"
    def git(self, args, cwd=None):
        r = subprocess.run(["git"] + args, cwd=cwd, env=self.git_env(), capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr).replace(self.auth, "***")

def emit(args, data, lines):
    if args.json: print(json.dumps(data, indent=2, default=str))
    else: print("\n".join(lines))

def short(ref): return re.sub(r"^refs/(heads|tags)/", "", ref or "")


# ---------------------------------------------------------------- discover
def cmd_discover(a, az):
    repo = az.repo(a.repo); rid = repo["id"]; d = {"repo": repo["name"], "project": az.project, "default_branch": short(repo.get("defaultBranch"))}
    L = [f"repository {repo['name']} (project {az.project}): default branch {d['default_branch']}", f"  clone url (no credentials): {az.remote(repo['name']).replace('/' + az.org + '/', '/<org>/')}"]
    # branches with last commit date
    stats = az.get(f"/_apis/git/repositories/{rid}/stats/branches").get("value", [])
    d["branches"] = [{"name": b["name"], "last_commit": (b.get("commit", {}).get("committer", {}).get("date") or "")[:10],
                      "ahead_of_default": b.get("aheadCount"), "behind_default": b.get("behindCount")} for b in stats]
    L.append(f"branches ({len(stats)}):")
    for b in sorted(d["branches"], key=lambda b: b["last_commit"], reverse=True):
        L.append(f"  {b['name']:40} last commit {b['last_commit']}  ahead {b['ahead_of_default']} behind {b['behind_default']}")
    tags = az.get(f"/_apis/git/repositories/{rid}/refs?filter=tags/&peelTags=true").get("value", [])
    d["tags"] = [short(t["name"]) for t in tags]; L.append("tags (%d): %s" % (len(tags), ", ".join(d["tags"]) or "none"))
    # branch policies
    pols = [p for p in az.get("/_apis/policy/configurations").get("value", [])
            if any(s.get("repositoryId") == rid for s in p.get("settings", {}).get("scope", []))]
    d["policies"] = [{"type": p["type"]["displayName"], "enabled": p["isEnabled"], "blocking": p["isBlocking"],
                      "branches": [short(s.get("refName") or "(all)") + (":" + s["matchKind"] if s.get("matchKind") == "Prefix" else "") for s in p["settings"]["scope"] if s.get("repositoryId") == rid]} for p in pols]
    L.append(f"branch policies ({len(pols)}): a branch with any policy takes pull requests only" if pols else "branch policies: none")
    for p in d["policies"]: L.append(f"  {p['type']} on {', '.join(p['branches'])} (blocking={p['blocking']}, enabled={p['enabled']})")
    # pull requests
    prs = az.get(f"/_apis/git/repositories/{rid}/pullrequests?searchCriteria.status=active&$top=50").get("value", [])
    d["open_pull_requests"] = [{"id": p["pullRequestId"], "title": p["title"], "source": short(p["sourceRefName"]), "target": short(p["targetRefName"])} for p in prs]
    L.append(f"open pull requests ({len(prs)}):")
    for p in d["open_pull_requests"]: L.append(f"  !{p['id']} {p['source']} -> {p['target']}: {p['title']}")
    # pipelines
    defs = az.get(f"/_apis/build/definitions?repositoryId={rid}&repositoryType=TfsGit&includeAllProperties=true").get("value", [])
    d["pipelines"] = []
    for b in defs:
        full = az.get(f"/_apis/build/definitions/{b['id']}")
        d["pipelines"].append({"name": b["name"], "id": b["id"], "yaml": full.get("process", {}).get("yamlFilename"), "folder": b.get("path")})
    L.append(f"pipelines ({len(defs)}):")
    for p in d["pipelines"]: L.append(f"  {p['name']} (id {p['id']}) YAML {p['yaml']}")
    # variable groups: names only
    vgs = az.get("/_apis/distributedtask/variablegroups").get("value", [])
    d["variable_groups"] = [{"name": g["name"], "variables": sorted(g.get("variables", {})), "secret": sorted(k for k, v in g.get("variables", {}).items() if v.get("isSecret"))} for g in vgs]
    L.append("variable groups (names only, never values):")
    for g in d["variable_groups"]: L.append(f"  {g['name']}: {', '.join(g['variables'])}  (secret: {', '.join(g['secret']) or 'none'})")
    sc = az.get("/_apis/serviceendpoint/endpoints").get("value", [])
    d["service_connections"] = [{"name": s["name"], "type": s["type"]} for s in sc]
    L.append("service connections: " + (", ".join(f"{s['name']} ({s['type']})" for s in d["service_connections"]) or "none"))
    pools = az.get("/_apis/distributedtask/pools", project=False).get("value", [])
    d["agent_pools"] = []; L.append("agent pools:")
    for p in pools:
        if p.get("isHosted"): continue
        ags = az.get(f"/_apis/distributedtask/pools/{p['id']}/agents?includeCapabilities=true", project=False).get("value", [])
        e = {"pool": p["name"], "agents": []}
        for g in ags:
            caps = g.get("systemCapabilities", {})
            tools = sorted(k for k in caps if k.lower() in ("java_home", "docker", "node", "python3", "git", "curl", "jq", "zip", "mvn", "maven", "gradle", "dotnet") or k.lower().startswith("java"))
            e["agents"].append({"name": g["name"], "status": g["status"], "os": caps.get("Agent.OS"), "capabilities": tools})
        d["agent_pools"].append(e)
        L.append(f"  pool {p['name']}: " + ("; ".join(f"agent {g['name']} {g['status']} {g['os']} caps[{', '.join(g['capabilities'])}]" for g in e["agents"]) or "no agents"))
    if not any(not p.get("isHosted") for p in pools): L.append("  (no self-hosted pools; Microsoft-hosted agents need granted parallelism)")
    envs = az.get("/_apis/distributedtask/environments").get("value", [])
    d["environments"] = [e["name"] for e in envs]; L.append("environments: " + (", ".join(d["environments"]) or "none"))
    # shared template repository
    try:
        t = az.get(f"/_apis/git/repositories/{TEMPLATE_REPO}")
        tt = [short(x["name"]) for x in az.get(f"/_apis/git/repositories/{t['id']}/refs?filter=tags/").get("value", [])]
        d["template_repository"] = {"name": TEMPLATE_REPO, "tags": tt}; L.append(f"shared template repository {TEMPLATE_REPO}: tags {', '.join(tt) or 'none (empty or untagged)'}")
    except SystemExit:
        d["template_repository"] = None; L.append(f"shared template repository {TEMPLATE_REPO}: not found in project {az.project}")
    emit(a, d, L)


# ---------------------------------------------------------------- git
def cmd_clone(a, az):
    if os.path.exists(a.dir) and os.listdir(a.dir): die(f"{a.dir} exists and is not empty")
    rc, out = az.git(["clone", az.remote(a.repo), a.dir])
    if rc: die("git clone failed: " + out[-400:], 1)
    print(f"cloned {a.repo} into {a.dir}")

def cmd_push(a, az):
    if not a.branch.startswith("veracode/"): die("push refuses any branch that does not start with veracode/ (this tool never writes to a team branch)")
    if not os.path.isdir(os.path.join(a.dir, ".git")): die(f"{a.dir} is not a git working copy")
    rc, remote = az.git(["remote", "get-url", "origin"], cwd=a.dir)
    if rc or "/_git/" not in remote: die("origin of this working copy is not an Azure DevOps repository")
    rc, out = az.git(["push", "origin", f"HEAD:refs/heads/{a.branch}"], cwd=a.dir)   # no --force, ever
    if rc: die("git push failed (rejected non-fast-forward? pick a new branch name): " + out[-500:], 1)
    print(f"pushed HEAD to {a.branch}"); print(out.strip()[-300:].replace(az.org, "<org>"))


# ---------------------------------------------------------------- pipelines
def pipeline_id(az, repo, name):
    defs = az.get(f"/_apis/build/definitions?name={urllib.parse.quote(name)}").get("value", [])
    rid = az.repo(repo)["id"]
    ok = [x for x in defs if x["name"] == name and x.get("repository", {}).get("id") in (rid, None)] or [x for x in defs if x["name"] == name]
    if not ok: die(f"no pipeline named {name!r} in project {az.project} (see: ado.py discover {repo})")
    return ok[0]["id"], rid

STEP_RE = re.compile(r"^(\s*)-?\s*(stage|job|deployment|displayName|template|checkout|publish|task|bash|script):\s*(.*)$")
def cmd_validate(a, az):
    pid, _ = pipeline_id(az, a.repo, a.pipeline)
    body = {"previewRun": True, "resources": {"repositories": {"self": {"refName": "refs/heads/" + a.branch.replace("refs/heads/", "")}}}}
    if a.file:
        try: body["yamlOverride"] = open(a.file).read()
        except OSError as e: die(f"cannot read {a.file}: {e}")
    r = az.call("POST", f"/_apis/pipelines/{pid}/preview", body)
    final = r.get("finalYaml") or ""
    names = []
    for line in final.splitlines():
        m = re.match(r"^(\s*)-?\s*(stage|job|deployment|displayName):\s*(.*)$", line)
        if m and (m.group(2) != "displayName" or True): names.append((len(m.group(1)), m.group(2), m.group(3).strip("'\"")))
    steps = [n for n in names]
    if a.json: print(json.dumps({"ok": True, "pipeline_id": pid, "names": [f"{k}: {v}" for _, k, v in steps]}, indent=2)); return
    print(f"OK: pipeline {a.pipeline!r} (id {pid}) expands on {a.branch}")
    for ind, k, v in steps: print(("  " if k in ("stage", "job", "deployment") else "    ") + f"{k}: {v}")

def build_by_id(az, bid): return az.get(f"/_apis/build/builds/{bid}")

def cmd_run(a, az):
    pid, _ = pipeline_id(az, a.repo, a.pipeline)
    r = az.call("POST", f"/_apis/pipelines/{pid}/runs", {"resources": {"repositories": {"self": {"refName": "refs/heads/" + a.branch.replace("refs/heads/", "")}}}})
    emit(a, {"run_id": r["id"], "state": r["state"]}, [f"queued run {r['id']} of {a.pipeline} on {a.branch} ({r['state']})"])

def cmd_runs(a, az):
    rid = az.repo(a.repo)["id"]
    q = f"/_apis/build/builds?repositoryId={rid}&repositoryType=TfsGit&queryOrder=queueTimeDescending&$top={a.top}"
    if a.branch: q += "&branchName=refs/heads/" + urllib.parse.quote(a.branch.replace("refs/heads/", ""))
    bs = az.get(q).get("value", [])
    rows = [{"id": b["id"], "pipeline": b["definition"]["name"], "branch": short(b["sourceBranch"]), "status": b.get("result") or b["status"], "commit": (b.get("sourceVersion") or "")[:8], "reason": b["reason"]} for b in bs]
    emit(a, rows, [f"{r['id']:>6} {r['status']:<18} {r['pipeline']:<24} {r['branch']:<36} {r['commit']} {r['reason']}" for r in rows] or ["no runs"])

def timeline(az, bid): return sorted(az.get(f"/_apis/build/builds/{bid}/timeline").get("records", []), key=lambda r: (r.get("order") or 0))

def cmd_run_wait(a, az):
    t0 = time.time()
    while True:
        b = build_by_id(az, a.id)
        if b["status"] == "completed": break
        if time.time() - t0 > a.timeout: die(f"run {a.id} still {b['status']} after {a.timeout} s (it keeps running; call run-wait again)", 3)
        time.sleep(15)
    res = b.get("result"); rec = timeline(az, a.id); byid = {r["id"]: r for r in rec}
    out = {"run_id": a.id, "result": res, "branch": short(b["sourceBranch"]), "commit": b.get("sourceVersion"), "records": []}
    L = [f"run {a.id} {res} on {short(b['sourceBranch'])} ({(b.get('sourceVersion') or '')[:8]}), pipeline {b['definition']['name']}"]
    kids = {}
    for r in rec: kids.setdefault(r.get("parentId"), []).append(r)
    def walk(parent, depth):
        for r in sorted(kids.get(parent, []), key=lambda r: r.get("order") or 0):
            if r["type"] not in ("Stage", "Job", "Task"): walk(r["id"], depth); continue
            if r["type"] == "Task" and r["name"] in ("Initialize job", "Finalize Job", "Checkout", "Post-job: Checkout") and r.get("result") == "succeeded": continue
            out["records"].append({"type": r["type"], "name": r["name"], "result": r.get("result"), "issues": [i["message"][:300] for i in r.get("issues") or []]})
            L.append("  " * (depth + 1) + f"{r['type']:5} {r['name']}: {r.get('result') or r.get('state')}")
            for i in r.get("issues") or []: L.append("  " * (depth + 2) + f"{i['type']}: {i['message'][:300]}")
            walk(r["id"], depth + 1)
    walk(None, 0)
    emit(a, out, L)
    sys.exit(0 if res in ("succeeded", "partiallySucceeded") else 1)

def fetch_text(az, url):
    return az.call("GET", url, raw=True).decode(errors="replace")

def cmd_run_log(a, az):
    rec = [r for r in timeline(az, a.id) if r["type"] == "Task" and r.get("log")]
    if a.step: sel = [r for r in rec if a.step.lower() in r["name"].lower()]
    else: sel = [r for r in rec if r.get("result") in ("failed", "succeededWithIssues", "canceled")]
    if not sel: die("no step matches" if a.step else "no step failed or had warnings (use --step TEXT)", 1)
    for r in sel:
        print(f"===== {r['name']} ({r.get('result')})"); txt = fetch_text(az, r["log"]["url"])
        print("\n".join(txt.splitlines()[-a.lines:]))

def cmd_artifact(a, az):
    j = az.get(f"/_apis/build/builds/{a.id}/artifacts?artifactName={urllib.parse.quote(a.name)}")
    url = (j.get("resource") or {}).get("downloadUrl")
    if not url: die(f"run {a.id} has no artifact {a.name!r}", 1)
    data = az.call("GET", url + ("&" if "?" in url else "?") + "$format=zip", raw=True)
    os.makedirs(a.dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        for n in names:
            if n.startswith("/") or ".." in n.split("/"): die("unsafe path in artifact zip")
        z.extractall(a.dir)
    top = names[0].split("/")[0] if names else ""
    print(f"artifact {a.name} of run {a.id}: {len(names)} files in {a.dir}" + (f" (under {top}/)" if top else ""))
    for n in names[:40]: print("  " + n)


# ---------------------------------------------------------------- pull requests
def cmd_pr_create(a, az):
    rid = az.repo(a.repo)["id"]
    try: desc = open(a.description_file).read()
    except OSError as e: die(f"cannot read {a.description_file}: {e}")
    r = az.call("POST", f"/_apis/git/repositories/{rid}/pullrequests",
                {"sourceRefName": "refs/heads/" + a.source, "targetRefName": "refs/heads/" + a.target, "title": a.title, "description": desc[:3900]})
    emit(a, {"id": r["pullRequestId"], "status": r["status"]}, [f"created pull request {r['pullRequestId']} ({a.source} -> {a.target}), status {r['status']}",
         f"  {az.remote(a.repo).replace('/' + az.org + '/', '/<org>/')}/pullrequest/{r['pullRequestId']}"])

def latest_run(az, rid, branch):
    bs = az.get(f"/_apis/build/builds?repositoryId={rid}&repositoryType=TfsGit&branchName=refs/heads/{urllib.parse.quote(branch)}&queryOrder=queueTimeDescending&$top=1").get("value", [])
    return bs[0] if bs else None

def pr_get(az, rid, pid): return az.get(f"/_apis/git/repositories/{rid}/pullrequests/{pid}")

def cmd_pr_status(a, az):
    rid = az.repo(a.repo)["id"]; p = pr_get(az, rid, a.id); src = short(p["sourceRefName"])
    b = latest_run(az, rid, src)
    d = {"id": a.id, "status": p["status"], "merge_status": p.get("mergeStatus"), "source": src, "target": short(p["targetRefName"]),
         "source_commit": p["lastMergeSourceCommit"]["commitId"], "latest_run": None if not b else {"id": b["id"], "status": b.get("result") or b["status"], "commit": b.get("sourceVersion")}}
    L = [f"pull request {a.id}: {p['status']}, merge {p.get('mergeStatus')}, {src} -> {d['target']}, source commit {d['source_commit'][:8]}"]
    L.append("  latest run of the source branch: " + (f"{b['id']} {d['latest_run']['status']} on commit {(b.get('sourceVersion') or '')[:8]}" + ("" if b.get("sourceVersion") == d["source_commit"] else "  (NOT the PR's source commit)") if b else "none"))
    emit(a, d, L)

def cmd_pr_complete(a, az):
    rid = az.repo(a.repo)["id"]; p = pr_get(az, rid, a.id)
    if p["status"] != "active": die(f"pull request {a.id} is {p['status']}", 1)
    src = short(p["sourceRefName"]); commit = p["lastMergeSourceCommit"]["commitId"]; b = latest_run(az, rid, src)
    if not b: die(f"refused: no run of {src} exists; wait for the branch run", 1)
    if b.get("sourceVersion") != commit: die(f"refused: the latest run ({b['id']}) is not on the PR's source commit {commit[:8]}; wait for or queue the run of that commit", 1)
    st = b.get("result") or b["status"]
    if st not in ("succeeded", "partiallySucceeded"): die(f"refused: latest run {b['id']} of {src} is {st}; it must be succeeded or partiallySucceeded", 1)
    if a.strategy not in STRATEGIES: die("strategy must be one of " + ", ".join(sorted(STRATEGIES)))
    body = {"status": "completed", "lastMergeSourceCommit": {"commitId": commit},
            "completionOptions": {"mergeStrategy": a.strategy, "deleteSourceBranch": True, "mergeCommitMessage": f"Merged PR {a.id}: {p['title']}"}}
    az.call("PATCH", f"/_apis/git/repositories/{rid}/pullrequests/{a.id}", body)
    for _ in range(20):
        time.sleep(3); p = pr_get(az, rid, a.id)
        if p["status"] == "completed": break
    if p["status"] != "completed":
        die(f"pull request {a.id} is still {p['status']} (merge {p.get('mergeStatus')}): a branch policy may need another strategy (try --strategy squash) or the merge has conflicts", 1)
    mc = (p.get("lastMergeCommit") or {}).get("commitId", "")
    emit(a, {"id": a.id, "status": "completed", "merge_commit": mc, "run": b["id"]}, [f"pull request {a.id} completed ({a.strategy}) on {short(p['targetRefName'])}, merge commit {mc[:8]}, gated by run {b['id']} ({st})"])


# ---------------------------------------------------------------- detect
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
def vkey(v): return tuple(int(x) for x in SEMVER.match(v).groups())

def cmd_detect(a, az_factory):
    files = []
    for root, dirs, names in os.walk(a.dir):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
        for n in names:
            if n.endswith((".yml", ".yaml")): files.append(os.path.join(root, n))
    alias = {}; ref_of = {}; mode = None; where = None; foreign = []
    for f in files:
        txt = open(f, errors="replace").read(); code = "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("#"))
        for m in re.finditer(r"(?m)^\s*-\s*repository:\s*(\S+)\s*\n((?:\s+.*\n?)*)", code):
            block = m.group(2)
            if re.search(r"name:\s*(?:[\w.-]+/)?" + TEMPLATE_REPO + r"\b", block):
                r = re.search(r"ref:\s*(\S+)", block); alias[m.group(1)] = r.group(1).strip("'\"") if r else "(no ref: default branch)"
        for m in re.finditer(r"(?m)^\s*-\s*template:\s*(\S*veracode-steps\.yml)(@(\S+))?\s*$", code):
            if m.group(3) and m.group(3) in alias: mode, where, ref_of = "template", f, alias[m.group(3)]
            elif not m.group(3) and mode is None: mode, where = "copy", f
        if re.search(r"(?i)task:\s*Veracode@|pipeline-scan\.jar|veracode\s+(static|scan)\b|vosp-api-wrappers|srcclr", code) and not f.endswith("veracode-steps.yml"):
            foreign.append(os.path.relpath(f, a.dir))
    latest = None
    try:
        az = az_factory()
        t = az.get(f"/_apis/git/repositories/{TEMPLATE_REPO}")
        tags = [short(x["name"]) for x in az.get(f"/_apis/git/repositories/{t['id']}/refs?filter=tags/").get("value", [])]
        tags = [x for x in tags if SEMVER.match(x)]; latest = max(tags, key=vkey) if tags else None
    except SystemExit: pass
    rel = os.path.relpath(where, a.dir) if where else None
    if mode == "template":
        ver = short(ref_of)
        if not SEMVER.match(ver): verdict, why = "upgrade", f"template pinned to {ref_of!r}, not an exact tag: pin it to a release tag"
        elif latest and vkey(ver) < vkey(latest): verdict, why = "upgrade", f"pinned {ver}, newest release {latest}: change the tag only"
        else: verdict, why = "nothing to do", f"pinned {ver}" + (f" = newest release {latest}" if latest else " (newest release not checked)")
    elif mode == "copy": verdict, why = "upgrade", f"in-repo copy called from {rel}: replace it by the shared template at {latest or 'its newest release'}, or leave it if the shared repository is out of reach"
    else:
        verdict, why = "not onboarded", "no call of veracode-steps.yml found" + (f"; other Veracode usage in: {', '.join(foreign)} (read it before adding anything)" if foreign else "")
    d = {"verdict": verdict, "mode": mode or "none", "file": rel, "version": short(ref_of) if mode == "template" else None, "latest": latest, "foreign_veracode_usage": foreign, "detail": why}
    emit(a, d, [f"mode: {d['mode']}" + (f" ({rel})" if rel else ""), f"version: {d['version']}  newest release: {latest}", verdict, "  " + why])


# ---------------------------------------------------------------- profile
def cmd_profile(a, az):
    cand = [os.path.join(HERE, "veracode_app_profile.py"), os.path.join(HERE, "..", "..", "veracode-repo-onboarding", "tools", "veracode_app_profile.py")]
    tool = next((c for c in cand if os.path.isfile(c)), None)
    if not tool: die("GAP: veracode_app_profile.py is not next to ado.py; there is no other profile tool. Create the profile in the Veracode UI or REST API (POST /appsec/v1/applications)", 1)
    r = subprocess.run([sys.executable, tool, "ensure" if a.create else "get", a.name], capture_output=True, text=True, env=os.environ)
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr[-500:]); sys.exit(r.returncode)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default="veracode-demo"); common.add_argument("--json", action="store_true")
    ap.add_argument("--project", default="veracode-demo"); ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    def add(name, fn, *pos, opts=()):
        p = sub.add_parser(name, parents=[common]); p.set_defaults(fn=fn)
        for x in pos: p.add_argument(x)
        for o, kw in opts: p.add_argument(o, **kw)
        return p
    add("discover", cmd_discover, "repo"); add("clone", cmd_clone, "repo", "dir"); add("push", cmd_push, "dir", "branch")
    add("validate", cmd_validate, "repo", "pipeline", "branch", opts=[("--file", {})])
    add("detect", cmd_detect, "dir")
    add("pr-create", cmd_pr_create, "repo", "source", "target", opts=[("--title", {"required": True}), ("--description-file", {"required": True})])
    add("pr-status", cmd_pr_status, "repo", "id", opts=[]); add("pr-complete", cmd_pr_complete, "repo", "id", opts=[("--strategy", {"default": "noFastForward"})])
    add("run", cmd_run, "repo", "pipeline", "branch")
    add("runs", cmd_runs, "repo", opts=[("--branch", {}), ("--top", {"type": int, "default": 10})])
    p = add("run-wait", cmd_run_wait, "id", opts=[("--timeout", {"type": int, "default": 3600})])
    add("run-log", cmd_run_log, "id", opts=[("--step", {}), ("--lines", {"type": int, "default": 80})])
    add("artifact", cmd_artifact, "id", "name", "dir")
    add("profile", cmd_profile, "name", opts=[("--create", {"action": "store_true"})])
    a = ap.parse_args()
    if a.cmd in ("run-wait", "run-log", "artifact", "pr-status", "pr-complete"): a.id = int(a.id)
    if a.cmd == "detect": a.fn(a, lambda: Az(a.project)); return
    if a.cmd == "profile": a.fn(a, None); return
    a.fn(a, Az(a.project))

if __name__ == "__main__":
    main()
