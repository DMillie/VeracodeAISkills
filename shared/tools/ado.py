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
                                              commit, ended succeeded or partiallySucceeded; a refusal prints the next command
                                              (REFUSED: ... Next: ...), and STOP after 3 refusals in a row for the same PR
  ado.py run <repo> <pipeline> <branch>       queue a run
  ado.py runs <repo> [--branch B] [--top N]   recent runs
  ado.py run-wait <id> [--timeout S]          loops until the run is final (S = optional cap); every poll prints elapsed minutes and why it waits
                                              (waiting for an agent | WAITING FOR PERMISSION); at the end stage/job/step results, warnings and
                                              VERACODE STEPS; exit 1 unless (partially) succeeded; exit 4 when a permission gate holds the run
  ado.py run-log <id> [--step TEXT]           log of the steps whose name contains TEXT (default: steps with issues or failures)
  ado.py artifact <id> <name> <dir>           download a pipeline artifact and unzip it into <dir>
  ado.py profile <name> [--create]            Veracode application profile by exact name (get; --create = get or create)
"""
import argparse, base64, contextlib, datetime, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request, zipfile

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
    if not getattr(a, "allow_no_veracode", False) and detect_dir(a.dir)["verdict"] == "not onboarded":
        print("REFUSED: this branch contains no Veracode template reference. Make the CI change first (playbook/05-ci-change-azure.md), validate it, then push.")
        sys.exit(1)
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
    bad = container_jobs(final)
    warn = [f"WARNING: job {j!r} runs the Veracode steps inside a container. The template needs the AGENT's tools (java, python3, jq, curl), "
            "which a build image usually lacks: the steps would fail with exit 127. Next: remove `container:` from that job "
            "(build in another job and hand the output over as a pipeline artifact, or use `docker run` with a pinned image)." for j in bad]
    if a.json: print(json.dumps({"ok": True, "pipeline_id": pid, "names": [f"{k}: {v}" for _, k, v in steps], "warnings": warn}, indent=2)); return
    print(f"OK: pipeline {a.pipeline!r} (id {pid}) expands on {a.branch}")
    for ind, k, v in steps: print(("  " if k in ("stage", "job", "deployment") else "    ") + f"{k}: {v}")
    for w in warn: print(w)

def container_jobs(final):
    """Names of jobs in an expanded pipeline YAML that have both a `container:` key and a step whose displayName starts 'Veracode:'."""
    blocks, cur = [], ["(pipeline)", []]
    for line in final.splitlines():
        m = re.match(r"^\s*-\s*(job|deployment):\s*(\S+)", line)
        if m: blocks.append(cur); cur = [m.group(2), []]
        cur[1].append(line)
    blocks.append(cur)
    out = []
    for name, lines in blocks:
        t = "\n".join(lines)
        if re.search(r"displayName:\s*['\"]?Veracode:", t) and re.search(r"(?m)^\s*container:", t) and not re.search(r"(?m)^\s*container:\s*['\"]?none", t): out.append(name)
    return out

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

def parse_ts(t):
    if not t: return None
    try:
        d = datetime.datetime.fromisoformat(re.sub(r"(\.\d{6})\d+", r"\1", t.replace("Z", "+00:00")))
        return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)
    except ValueError: return None

def elapsed_minutes(b, t0):
    q = parse_ts(b.get("queueTime"))
    secs = (datetime.datetime.now(datetime.timezone.utc) - q).total_seconds() if q else time.time() - t0
    return max(0, int(secs // 60))

GATE_KINDS = re.compile(r"(repositor(?:y|ies)|variable group|service connection|secure file|environment|agent pool|queue|pool)\W+(?:named\s+)?['\"]?([\w./ -]{1,60})", re.I)
def permission_gate(rec):
    """Description of an uncompleted Checkpoint.Authorization record in the timeline, or None."""
    byid = {r["id"]: r for r in rec}
    for r in rec:
        if "Checkpoint.Authorization" in (r.get("type"), r.get("name")) and r.get("state") != "completed":
            text = " ".join(i.get("message", "") for i in (r.get("issues") or []) + (byid.get(r.get("parentId"), {}).get("issues") or []))
            m = GATE_KINDS.search(text)
            if m: return f"{m.group(1)} {m.group(2).strip()}"
            p = byid.get(r.get("parentId")) or {}
            return "resource of " + (byid.get(p.get("parentId"), p).get("name") or "this run") + " (the run page names it)"
    return None

def jobs_ahead(az, b):
    """(unfinished job requests queued before this run, pool name) in the self-hosted pool that holds this run's job
    request; (None, None) when unreadable or the job has no request yet."""
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            pools = [p for p in az.get("/_apis/distributedtask/pools", project=False).get("value", []) if not p.get("isHosted")]
            for p in pools:
                reqs = az.get(f"/_apis/distributedtask/pools/{p['id']}/jobrequests", project=False).get("value", [])
                openr = [r for r in reqs if not r.get("result")]
                mine = [r for r in openr if (r.get("owner") or {}).get("id") == b["id"]]
                if not mine: continue
                mq = min(r.get("queueTime") or "~" for r in mine)
                return len([r for r in openr if r not in mine and (r.get("queueTime") or "~") < mq]), p["name"]
    except SystemExit: pass
    return None, None

def wait_reason(az, b, rec):
    """('permission'|'agent'|'running', one line) for a run that is not final."""
    gate = permission_gate(rec)
    if gate: return "permission", f"WAITING FOR PERMISSION: {gate}: a person must click Permit on the run page"
    active = [r for r in rec if r.get("type") == "Task" and r.get("state") == "inProgress"]
    if active: return "running", f"running: {active[0]['name']}"
    n, pool = jobs_ahead(az, b)
    if n is None: return "agent", "waiting for an agent"
    return "agent", f"waiting for an agent ({n} jobs ahead in pool {pool})"

def veracode_steps(rec):
    """One (name, text) per Veracode step: ran / skipped by placement / skipped after a failure / warning text."""
    byid = {r["id"]: r for r in rec}; out = []
    for r in sorted(rec, key=lambda r: r.get("order") or 0):
        if r.get("type") != "Task" or not (r.get("name") or "").lower().startswith("veracode"): continue
        res = r.get("result")
        msg = "; ".join(i["message"][:200] for i in r.get("issues") or [])
        if res == "skipped":
            before = [x for x in rec if x.get("type") == "Task" and x.get("parentId") == r.get("parentId") and (x.get("order") or 0) < (r.get("order") or 0)
                      and (x.get("result") in ("failed", "canceled") or any(i.get("type") == "error" for i in x.get("issues") or []))]
            text = "skipped after a failure" if before else "skipped by placement"
        elif res in ("succeededWithIssues", "failed", "canceled"): text = f"{'warning' if res == 'succeededWithIssues' else res}: {msg or 'see run-log'}"
        elif res == "succeeded": text = "ran"
        else: text = res or r.get("state") or "no result"
        out.append((r["name"], text))
    return out

def cmd_run_wait(a, az):
    t0 = time.time(); gate_polls = 0
    while True:
        b = build_by_id(az, a.id)
        if b["status"] == "completed": break
        kind, why = wait_reason(az, b, timeline(az, a.id))
        print(f"[{elapsed_minutes(b, t0)} min] run {a.id} {b['status']}: {why}", flush=True)
        gate_polls = gate_polls + 1 if kind == "permission" else 0
        if gate_polls >= 2: print("A person must act. Tell them; do not retry the run. (exit 4)"); sys.exit(4)
        if a.timeout and time.time() - t0 > a.timeout: die(f"run {a.id} still {b['status']} after {a.timeout} s (it keeps running; call run-wait again)", 3)
        time.sleep(a.interval)
    res = b.get("result"); rec = timeline(az, a.id)
    out = {"run_id": a.id, "result": res, "branch": short(b["sourceBranch"]), "commit": b.get("sourceVersion"), "elapsed_minutes": elapsed_minutes(b, t0), "records": []}
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
    vs = veracode_steps(rec); out["veracode_steps"] = [{"step": n, "state": t} for n, t in vs]
    L.append("VERACODE STEPS:")
    L += [f"  {n}: {t}" for n, t in vs] or ["  (no step with Veracode in its name: the Veracode change did not run in this run)"]
    L.append(f"elapsed {out['elapsed_minutes']} min. A green colour proves nothing: open artifact veracode-results and require results.json (playbook 06).")
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

def refusal_counter(az, repo, pid, bump=None):
    """Refusals in a row for this repo and PR, kept in a small file in the temp dir. bump=True adds one, False resets."""
    f = os.path.join(tempfile.gettempdir(), "ado-pr-refusals-" + hashlib.sha1(f"{az.project}/{repo}/{pid}".encode()).hexdigest()[:16])
    try: n = int(open(f).read().strip() or 0) if time.time() - os.path.getmtime(f) < 3600 else 0   # a count older than an hour is from another session
    except (OSError, ValueError): n = 0
    if bump is False:
        with contextlib.suppress(OSError): os.remove(f)
        return 0
    if bump:
        n += 1
        with contextlib.suppress(OSError): open(f, "w").write(str(n))
    return n

def pr_refuse(a, az, what, nxt):
    n = refusal_counter(az, a.repo, a.id, bump=True)
    print(f"REFUSED: {what}. Next: {nxt} Do not call pr-complete again before that is done.")
    if n >= 3: print("STOP: you are repeating a refused call.")
    sys.exit(1)

def cmd_pr_complete(a, az):
    rid = az.repo(a.repo)["id"]; p = pr_get(az, rid, a.id)
    if p["status"] != "active": pr_refuse(a, az, f"pull request {a.id} is {p['status']}", f"ado.py pr-status {a.repo} {a.id}; there is nothing left to complete.")
    src = short(p["sourceRefName"]); commit = p["lastMergeSourceCommit"]["commitId"]; b = latest_run(az, rid, src)
    if not b: pr_refuse(a, az, f"no run of {src} exists", f"ado.py runs {a.repo} --branch {src} (the push should have queued one; see ado.py discover {a.repo} for the pipeline name).")
    if b.get("sourceVersion") != commit:
        pr_refuse(a, az, f"latest run {b['id']} on {src} is not on the PR's source commit {commit[:8]}", f"ado.py runs {a.repo} --branch {src}, then ado.py run-wait <the run whose commit is {commit[:8]}>.")
    st = b.get("result") or b["status"]
    if st not in ("succeeded", "partiallySucceeded"):
        if b["status"] != "completed": pr_refuse(a, az, f"latest run on {src} is {st} (run {b['id']})", f"ado.py run-wait {b['id']}.")
        pr_refuse(a, az, f"latest run {b['id']} on {src} is {st}", f"ado.py run-log {b['id']}, find the cause, fix it on the branch (a new push starts a new run); at most two runs per branch.")
    if a.strategy not in STRATEGIES: die("strategy must be one of " + ", ".join(sorted(STRATEGIES)))
    body = {"status": "completed", "lastMergeSourceCommit": {"commitId": commit},
            "completionOptions": {"mergeStrategy": a.strategy, "deleteSourceBranch": True, "mergeCommitMessage": f"Merged PR {a.id}: {p['title']}"}}
    az.call("PATCH", f"/_apis/git/repositories/{rid}/pullrequests/{a.id}", body)
    for _ in range(20):
        time.sleep(3); p = pr_get(az, rid, a.id)
        if p["status"] == "completed": break
    if p["status"] != "completed":
        pr_refuse(a, az, f"pull request {a.id} is still {p['status']} (merge {p.get('mergeStatus')})", f"ado.py pr-complete {a.repo} {a.id} --strategy squash once (a branch policy may need another strategy); if it fails again the merge has conflicts: ask a person.")
    refusal_counter(az, a.repo, a.id, bump=False)
    mc = (p.get("lastMergeCommit") or {}).get("commitId", "")
    emit(a, {"id": a.id, "status": "completed", "merge_commit": mc, "run": b["id"]}, [f"pull request {a.id} completed ({a.strategy}) on {short(p['targetRefName'])}, merge commit {mc[:8]}, gated by run {b['id']} ({st})"])


# ---------------------------------------------------------------- detect
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
def vkey(v): return tuple(int(x) for x in SEMVER.match(v).groups())

def detect_dir(dirname, az_factory=None):
    """The detect check on a directory; az_factory=None skips the lookup of the newest release."""
    files = []
    for root, dirs, names in os.walk(dirname):
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
            foreign.append(os.path.relpath(f, dirname))
    latest = None
    try:
        az = az_factory()  # None: no lookup
        t = az.get(f"/_apis/git/repositories/{TEMPLATE_REPO}")
        tags = [short(x["name"]) for x in az.get(f"/_apis/git/repositories/{t['id']}/refs?filter=tags/").get("value", [])]
        tags = [x for x in tags if SEMVER.match(x)]; latest = max(tags, key=vkey) if tags else None
    except (SystemExit, TypeError): pass
    rel = os.path.relpath(where, dirname) if where else None
    if mode == "template":
        ver = short(ref_of)
        if not SEMVER.match(ver): verdict, why = "upgrade", f"template pinned to {ref_of!r}, not an exact tag: pin it to a release tag"
        elif latest and vkey(ver) < vkey(latest): verdict, why = "upgrade", f"pinned {ver}, newest release {latest}: change the tag only"
        else: verdict, why = "nothing to do", f"pinned {ver}" + (f" = newest release {latest}" if latest else " (newest release not checked)")
    elif mode == "copy": verdict, why = "upgrade", f"in-repo copy called from {rel}: replace it by the shared template at {latest or 'its newest release'}, or leave it if the shared repository is out of reach"
    else:
        verdict, why = "not onboarded", "no call of veracode-steps.yml found" + (f"; other Veracode usage in: {', '.join(foreign)} (read it before adding anything)" if foreign else "")
    return {"verdict": verdict, "mode": mode or "none", "file": rel, "version": short(ref_of) if mode == "template" else None, "latest": latest, "foreign_veracode_usage": foreign, "detail": why}

def cmd_detect(a, az_factory):
    d = detect_dir(a.dir, az_factory); rel, verdict, why, latest = d["file"], d["verdict"], d["detail"], d["latest"]
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
    add("discover", cmd_discover, "repo"); add("clone", cmd_clone, "repo", "dir")
    add("push", cmd_push, "dir", "branch", opts=[("--allow-no-veracode", {"action": "store_true", "help": "push although detect says not onboarded (the branch has no Veracode template reference); only for the rare legitimate case"})])
    add("validate", cmd_validate, "repo", "pipeline", "branch", opts=[("--file", {})])
    add("detect", cmd_detect, "dir")
    add("pr-create", cmd_pr_create, "repo", "source", "target", opts=[("--title", {"required": True}), ("--description-file", {"required": True})])
    add("pr-status", cmd_pr_status, "repo", "id", opts=[]); add("pr-complete", cmd_pr_complete, "repo", "id", opts=[("--strategy", {"default": "noFastForward"})])
    add("run", cmd_run, "repo", "pipeline", "branch")
    add("runs", cmd_runs, "repo", opts=[("--branch", {}), ("--top", {"type": int, "default": 10})])
    p = add("run-wait", cmd_run_wait, "id", opts=[("--timeout", {"type": int, "default": 0, "help": "optional cap in seconds; default: wait until the run is final"}), ("--interval", {"type": int, "default": 30, "help": "seconds between polls"})])
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
