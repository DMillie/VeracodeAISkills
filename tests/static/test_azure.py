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
done()
