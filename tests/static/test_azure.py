#!/usr/bin/env python3
"""Azure DevOps skill: layout, every file the documents name exists, every ado.py subcommand they
mention is in the agreed list, the decisive rules are present, the YAML it tells the agent to add is safe."""
import glob, os, re
from _common import *
S = os.path.join(ROOT, "veracode-azure-devops-onboarding")
SUBCOMMANDS = {"discover", "clone", "push", "validate", "detect", "pr-create", "pr-status", "pr-complete",
               "run", "runs", "run-wait", "run-log", "artifact", "profile"}
docs = sorted(glob.glob(S + "/**/*.md", recursive=True))
AZ = ("-azure.md", "/SKILL.md", "/AGENTS.md", "/repo-plan.md", "/repo-summary.md", "/azure-devops.md")
own = [f for f in docs if f.endswith(AZ)]   # the shared neutral and GitLab-era files are checked by sync_shared.py
text = {f: open(f, encoding="utf-8").read() for f in docs}
rel = lambda f: os.path.relpath(f, S)

check("skill folder exists with SKILL.md and AGENTS.md", all(os.path.isfile(os.path.join(S, n)) for n in ("SKILL.md", "AGENTS.md")))
skill = text.get(os.path.join(S, "SKILL.md"), "")
m = re.search(r"(?m)^description:\s*(.*)$", skill); d = m.group(1) if m else ""
check("description claims Azure DevOps, Azure Pipelines and Azure Repos", all(w in d for w in ("Azure DevOps", "Azure Pipelines", "Azure Repos")))
check("description points GitLab asks to the GitLab skill", "veracode-repo-onboarding" in d)
gl = open(os.path.join(ROOT, "veracode-repo-onboarding/SKILL.md")).read().split("---")[1]
check("the GitLab skill's description does not claim Azure", "azure" not in gl.lower())

# every path the documents name exists (the integration research snapshot and shared GitLab text are skipped)
PATH = re.compile(r"`((?:playbook|reference|templates|tools)/[A-Za-z0-9_./-]+)`")
ignore = {l.split()[1][1:] for l in open(os.path.join(ROOT, "shared/manifest.txt")) if l.startswith("veracode-azure-devops-onboarding !")}
missing = set()
for f in own:
    for p in PATH.findall(text[f]):
        p = p.rstrip(".")
        if "<" in p or "*" in p or p in ignore: continue
        if not os.path.exists(os.path.join(S, p)): missing.add(f"{rel(f)} -> {p}")
check("every file the documents name exists", not missing, "; ".join(sorted(missing)[:6]))
links = set()
for f in own:
    for l in re.findall(r"\]\(([A-Za-z0-9_.-]+\.md)\)", text[f]):
        if not os.path.exists(os.path.join(os.path.dirname(f), l)): links.add(f"{rel(f)} -> {l}")
check("every relative link between playbook files resolves", not links, "; ".join(sorted(links)))
for need in ("playbook/00-integration-ladder-azure.md", "playbook/01-intake-azure.md", "playbook/02-discovery-azure.md",
             "playbook/03-scan-placement-azure.md", "playbook/05-ci-change-azure.md", "playbook/06-verification-azure.md",
             "reference/facts/azure-devops.md", "templates/repo-plan.md", "templates/repo-summary.md",
             "tools/ado.py", "tools/scan-check.js", "tools/pipeline_scan_summary.py", "tools/veracode_app_profile.py"):
    check(f"{need} present", os.path.isfile(os.path.join(S, need)))
check("template content (templates/azure/) delivered", os.path.isdir(os.path.join(S, "templates/azure")) and bool(os.listdir(os.path.join(S, "templates/azure"))))

# ado.py subcommands named in the documents
named = {}
for f in own:
    for c in re.findall(r"ado\.py\s+(?:--\w+\s+\S+\s+)*([a-z][a-z-]+)", text[f]): named.setdefault(c, f)
bad = {c: rel(f) for c, f in named.items() if c not in SUBCOMMANDS}
check(f"every ado.py subcommand named is in the agreed list ({len(named)} named)", not bad, str(bad))
check("the documents use most of the tool (discover, clone, validate, detect, pr-create, run-wait, artifact, profile)",
      {"discover", "clone", "validate", "detect", "pr-create", "run-wait", "artifact", "profile"} <= set(named))
ado = os.path.join(S, "tools/ado.py")
if os.path.isfile(ado):
    src = open(ado).read(); absent = [c for c in sorted(named) if f'"{c}"' not in src]
    check("ado.py defines every subcommand the documents name", not absent, str(absent))

# the Azure documents carry no GitLab-only instruction
az = own
leak = [rel(f) for f in az if re.search(r"gitlab-ci-lint|detect_integration|\.gitlab-ci\.yml|merge request", text[f].replace("`.gitlab-ci.yml` in", "")) and not f.endswith(("SKILL.md",))]
check("Azure-specific documents name no GitLab tool or file as an instruction", not leak, str(leak))

# rules that must be present
def has(f, pat): return re.search(pat, re.sub(r"\s+", " ", text.get(os.path.join(S, f), "")), re.I) is not None
for f, pat, why in [
    ("SKILL.md", r"Never handle a credential value", "credentials"),
    ("SKILL.md", r"Additions only", "additive change"),
    ("SKILL.md", r"never write a REST call yourself", "one tool for Azure DevOps calls"),
    ("SKILL.md", r"Each branch has its own copy of the YAML", "one pull request per long-lived branch"),
    ("SKILL.md", r"branch with any policy accepts a pull request only", "protected branch"),
    ("SKILL.md", r"never a branch, never .latest", "pinned by tag"),
    ("SKILL.md", r"A green scan is not proof", "packaging proof"),
    ("SKILL.md", r"It does not see a missing variable group or a permission gate", "lint limits"),
    ("SKILL.md", r"Accepted upload is not completed scan", "report only what was verified"),
    ("SKILL.md", r"Untested", "untested list"),
    ("SKILL.md", r"waiting for permission", "permission gate is a stop"),
    ("playbook/00-integration-ladder-azure.md", r"unconfirmed", "extension collision stays unconfirmed"),
    ("playbook/00-integration-ladder-azure.md", r"SAME project", "template repository fence"),
    ("playbook/05-ci-change-azure.md", r"0 deleted lines", "additions only check"),
    ("playbook/05-ci-change-azure.md", r"At most two runs per branch", "run budget"),
    ("playbook/05-ci-change-azure.md", r"does not see a missing variable group", "lint limits"),
    ("playbook/06-verification-azure.md", r"verdict not read", "submitted is not verified"),
    ("reference/facts/azure-devops.md", r"UNCONFIRMED", "collision flagged"),
    ("reference/facts/azure-devops.md", r"Not run at all", "honest limits"),
]: check(f"{f}: {why}", has(f, pat), pat)

# YAML the playbook tells the agent to add
p5 = text.get(os.path.join(S, "playbook/05-ci-change-azure.md"), "")
blocks = re.findall(r"```yaml\n(.*?)```", p5, re.S); code = "\n".join(blocks)
check("05 has YAML for resources, shapes A, B, C, rung 2 and rung 3", len(blocks) >= 6, str(len(blocks)))
check("template pinned by tag, never a branch", "ref: refs/tags/" in code and not re.search(r"ref:\s*(refs/heads|main)", code))
check("no tab characters in the YAML", "\t" not in code)
check("no credential-looking value in the YAML", not re.search(r"(?i)(secret|key|token|pat)\s*[:=]\s*['\"]?[A-Za-z0-9]{20,}", code))
check("no :latest, no download piped into a shell", not re.search(r":latest\b|(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b", code))
check("every Veracode step the YAML adds is named 'Veracode: ...'", all(re.search(r"displayName: '(Veracode[^']*)'", b) for b in blocks if "- script:" in b or "- task:" in b)
      and all(n.startswith(("Veracode:", "Veracode (", "Veracode'")) or n in ("Veracode", "Veracode (upload only)") for n in re.findall(r"displayName: '([^']*)'", code)))
check("the group goes on the new job in shapes B and C, and rung 3 forbids it", len(re.findall(r"(?m)^\s+variables:\n\s+- group: veracode", code)) >= 2 and "must NOT load the group" in p5)
check("the template parameters of the built template are all named in the playbooks", all(k in p5 + text.get(os.path.join(S, "playbook/03-scan-placement-azure.md"), "") for k in ("sourceDir", "rolloutStage")))
tpl = os.path.join(S, "templates/azure/veracode-steps.yml")
if os.path.isfile(tpl):
    names = set(re.findall(r"(?m)^  - name: (\w+)", open(tpl).read()))
    used = set(re.findall(r"(?m)^\s+(\w+): ", "\n".join(re.findall(r"parameters:\n((?:\s+.*\n)+?)(?=\S|```|\n)", code + "\n"))))
    check("every parameter the playbook YAML passes exists in veracode-steps.yml", used <= names, str(used - names))
check("the new job has no container", "container:" not in code)
check("rung 3 task has createProfile false and does not fail the build on policy", "createProfile: false" in code and "failBuildOnPolicyFail: false" in code)
# parameter names the SPEC fixes
for k in ("appProfile", "policyScanRefs", "sandboxRefs", "staticScan", "directoryScan", "scaAgent", "artifactName", "package"):
    check(f"parameter {k} is used in the placement or change playbook", k in p5 or k in text.get(os.path.join(S, "playbook/03-scan-placement-azure.md"), ""))
try:
    import yaml
    for i, b in enumerate(blocks):
        if "<" in b: continue
        try: yaml.safe_load(b); ok = True
        except Exception as e: ok = False
        check(f"YAML block {i} parses", ok)
except ImportError: pass
# ---- ado.py behaviour, offline (fake service object, fake directory): run-wait reasons, pr-complete refusals, push refusal
import contextlib, importlib.util, io, subprocess, sys, tempfile
if os.path.isfile(ado):
    spec = importlib.util.spec_from_file_location("ado_under_test", ado); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    tmp = tempfile.mkdtemp(); tempfile.tempdir = tmp   # the refusal counter file lives in the temp dir
    class Fake:
        org, project = "o", "p"
        def __init__(self, routes): self.routes = routes
        def get(self, path, **kw):
            for k, v in self.routes.items():
                if k in path: return v() if callable(v) else v
            raise AssertionError("unexpected call " + path)
        repo = lambda self, n: {"id": "rid", "name": n}
        def call(self, *a, **kw): raise AssertionError("must not write")
    def run(fn, *args):
        out = io.StringIO(); code = None
        with contextlib.redirect_stdout(out):
            try: fn(*args)
            except SystemExit as e: code = e.code
        return code, out.getvalue()
    NS = lambda **k: type("NS", (), k)()
    # item 4: pr-complete refuses with the next command, STOP on the 3rd refusal in a row
    pr = {"status": "active", "sourceRefName": "refs/heads/veracode/x", "title": "t", "lastMergeSourceCommit": {"commitId": "c" * 40}}
    az = Fake({"pullrequests/7": pr, "builds?": {"value": [{"id": 123, "status": "inProgress", "sourceVersion": "c" * 40}]}})
    a = NS(repo="r", id=7, strategy="noFastForward", json=False)
    outs = [run(mod.cmd_pr_complete, a, az) for _ in range(3)]
    check("pr-complete refusal prints REFUSED with the exact next command", outs[0][0] == 1 and "REFUSED: latest run on veracode/x is inProgress (run 123). Next: ado.py run-wait 123." in outs[0][1] and "Do not call pr-complete again" in outs[0][1], outs[0][1])
    check("pr-complete prints STOP only from the 3rd refusal in a row", "STOP" not in outs[0][1] + outs[1][1] and "STOP: you are repeating a refused call." in outs[2][1], str([o[1][-60:] for o in outs]))
    # item 5: push refuses a branch without a Veracode reference; the override exists only in --help
    d = tempfile.mkdtemp(); os.makedirs(d + "/.git")
    open(d + "/azure-pipelines.yml", "w").write("trigger: [main]\nsteps:\n  - script: echo hi\n")
    env = dict(os.environ, AZURE_DEVOPS_ORG="testorg", AZURE_DEVOPS_PAT="dummy-test-value")
    sh = lambda *x: subprocess.run([sys.executable, ado] + list(x), capture_output=True, text=True, env=env)
    r = sh("push", d, "veracode/x")
    check("push refuses a directory with no Veracode template reference", r.returncode == 1 and "REFUSED: this branch contains no Veracode template reference. Make the CI change first (playbook/05-ci-change-azure.md), validate it, then push." in r.stdout, r.stdout + r.stderr)
    r = sh("push", d, "veracode/x", "--allow-no-veracode")
    check("--allow-no-veracode gets past the Veracode check", "REFUSED" not in r.stdout, r.stdout)
    open(d + "/azure-pipelines.yml", "a").write("resources:\n  repositories:\n    - repository: veracode\n      name: veracode-pipelines\n      ref: refs/tags/v1.0.0\n  - template: veracode-steps.yml@veracode\n")
    open(d + "/azure-pipelines.yml", "w").write("resources:\n  repositories:\n    - repository: veracode\n      type: git\n      name: veracode-pipelines\n      ref: refs/tags/v1.0.0\nsteps:\n  - template: veracode-steps.yml@veracode\n")
    r = sh("push", d, "veracode/x")
    check("push does not refuse a directory that calls the template", "REFUSED" not in r.stdout, r.stdout)
    check("--allow-no-veracode is documented in --help only", "--allow-no-veracode" in sh("push", "--help").stdout
          and not any("allow-no-veracode" in t for t in text.values()))
    # item 2: run-wait says why a run waits, and lists Veracode steps at the end
    rec = lambda **k: dict({"id": "r", "type": "Task", "name": "x", "order": 1}, **k)
    b = {"id": 5, "status": "notStarted", "queueTime": "2026-01-01T00:00:00.1234567Z"}
    kind, why = mod.wait_reason(Fake({"pools": {"value": []}}), b, [rec(id="j", type="Job", state="pending")])
    check("run-wait names a run that waits for the agent", kind == "agent" and why == "waiting for an agent", why)
    class Pools(Fake):
        def get(self, path, **kw):
            if "jobrequests" in path: return {"value": [{"queueTime": "2026-01-01T00:00:00Z", "owner": {"id": 9}}, {"queueTime": "2026-01-01T00:01:00Z", "owner": {"id": 5}}, {"queueTime": "2026-01-01T00:02:00Z", "owner": {"id": 8}}]}
            return {"value": [{"id": 1, "name": "Default"}]}
    check("run-wait counts the jobs ahead in the pool", mod.wait_reason(Pools({}), b, [])[1] == "waiting for an agent (1 jobs ahead in pool Default)", mod.wait_reason(Pools({}), b, [])[1])
    gate = [rec(id="c", type="Checkpoint.Authorization", state="inProgress", name="Checkpoint.Authorization", parentId="s", issues=[{"type": "warning", "message": "Pipeline needs permission to access repository veracode-pipelines"}]), rec(id="s", type="Stage", name="veracode")]
    kind, why = mod.wait_reason(Fake({}), b, gate)
    check("run-wait names a permission gate with resource type and name", kind == "permission" and why == "WAITING FOR PERMISSION: repository veracode-pipelines: a person must click Permit on the run page", why)
    gate[0]["state"] = "completed"
    check("a completed Checkpoint.Authorization is not a gate", mod.wait_reason(Pools({}), b, gate)[0] == "agent")
    steps = mod.veracode_steps([rec(id="a", parentId="j", order=1, name="Veracode: take the packaged jar", result="succeededWithIssues", issues=[{"type": "error", "message": "cp failed"}]),
                                rec(id="b", parentId="j", order=2, name="Veracode: Pipeline Scan", result="skipped"), rec(id="c", parentId="j", order=3, name="Checkout x@veracode/y", result="succeeded"),
                                rec(id="d", parentId="k", order=4, name="Veracode: policy or sandbox scan", result="skipped"), rec(id="e", parentId="k", order=5, name="Veracode: package", result="succeeded")])
    check("VERACODE STEPS: ran / warning / skipped after a failure / skipped by placement", [t for _, t in steps] == ["warning: cp failed", "skipped after a failure", "skipped by placement", "ran"], str(steps))
    tl = {"records": [{"id": "j", "type": "Job", "name": "veracode", "result": "succeededWithIssues", "order": 1}, {"id": "a", "parentId": "j", "type": "Task", "order": 2, "name": "Veracode: Pipeline Scan", "result": "succeededWithIssues", "issues": [{"type": "warning", "message": "no results.json"}]}]}
    calls = []
    def builds():
        calls.append(1); return {"id": 5, "status": "inProgress" if len(calls) < 3 else "completed", "result": "partiallySucceeded", "sourceBranch": "refs/heads/b", "queueTime": "2026-01-01T00:00:00Z", "definition": {"name": "d"}}
    mod.time.sleep = lambda s: None
    code, out = run(mod.cmd_run_wait, NS(id=5, timeout=0, interval=0, json=False), Fake({"timeline": tl, "builds/5": builds, "distributedtask/pools": {"value": []}}))
    check("run-wait loops until final by default, prints elapsed minutes and a VERACODE STEPS list", code == 0 and len(calls) == 3 and "min] run 5 inProgress: waiting for an agent" in out and "VERACODE STEPS:\n  Veracode: Pipeline Scan: warning: no results.json" in out, out)
done()
