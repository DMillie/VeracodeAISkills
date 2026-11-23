#!/usr/bin/env python3
"""(d) Rollout-stage logic for audit / warn / block-new / block-policy.
1. Render the component through the lint API once per stage (merged YAML): the stage reaches every
   job as VERACODE_ROLLOUT_STAGE, the gate jobs allow only exit code 42, informational jobs never block.
2. Take the rendered gate scripts and execute them with stubbed `java` and `curl` for every
   combination of stage x baseline x findings x criteria, and assert the exit code and the options
   handed to pipeline-scan.jar. No Veracode call is made; the scripts under test are the released ones."""
import os, re, stat, subprocess, tempfile
from _common import *
if not (TOKEN and URL and LINT_PROJECT): skip("set GITLAB_URL, GITLAB_TOKEN and LINT_PROJECT (a project the token can lint in)")
ver = component_version()
SRC = ("include:\n  - component: $CI_SERVER_FQDN/%s/veracode@%s\n    inputs:\n      app_name: demo-app\n      sca_image: python:3.11\n"
       "      rollout_stage: %s\n      baseline_map: 'hotfix/*=main,*=develop'\n%sveracode-package:\n  script: ['true']\n")
STAGES = ["audit", "warn", "block-new", "block-policy"]
scripts = {}
for s in STAGES:
    out = lint(SRC % (COMPONENT_PROJECT, ver, s, ""))
    check(f"{s}: renders valid", bool(out.get("valid")), str(out.get("errors")))
    if not out.get("valid"): continue
    my = out.get("merged_yaml", ""); jobs = {j["name"]: j for j in out["jobs"]}
    n = len(re.findall(rf"VERACODE_ROLLOUT_STAGE: {re.escape(s)}\b", my))
    check(f"{s}: VERACODE_ROLLOUT_STAGE={s} on all 8 jobs (found {n})", n >= 8 and not [x for x in STAGES if x != s and re.search(rf"VERACODE_ROLLOUT_STAGE: {re.escape(x)}\s", my)])
    def block(job): return re.search(rf"(?ms)^{job}:\n(.*?)(?=^\S|\Z)", my).group(1)
    for g in ("veracode-pipeline-scan", "veracode-policy-scan", "veracode-policy-resolve"):
        b = block(g); check(f"{s}: {g} allows only exit code 42", bool(re.search(r"allow_failure:\s*\n\s+exit_codes:\s*\n\s+- 42", b)), b[:200])
    for g in ("veracode-baseline", "veracode-sandbox-scan", "veracode-sca", "veracode-cli-directory-scan", "veracode-container-scan"):
        check(f"{s}: {g} is informational (allow_failure: true)", bool(re.search(r"(?m)^\s+allow_failure: true\s*$", block(g))))
    scripts[s] = {g: "\n".join(jobs[g]["script"]) for g in ("veracode-pipeline-scan", "veracode-policy-scan")}
out = lint(SRC % (COMPONENT_PROJECT, ver, "audit", ""))
check("default stage is audit when the input is omitted", "VERACODE_ROLLOUT_STAGE: audit" in lint((SRC % (COMPONENT_PROJECT, ver, "X", "")).replace("      rollout_stage: X\n", "")).get("merged_yaml", ""))

JAVA = r'''#!/bin/sh
echo "$@" >> "$STUB_DIR/java.args"
case " $* " in
  *" --request_policy "*) if [ "$FAKE_POLICY_KIND" = custom ]; then echo '{}' > Custom_Policy.json; exit 0; else echo "Builtin policies cannot be downloaded"; exit 255; fi;;
  *" UploadAndScan "*) exit "$FAKE_WRAPPER_RC";;
  *" --file "*) [ "$FAKE_SCAN_ERROR" = yes ] && exit 255; echo '{"findings":[]}' > results.json
     case " $* " in *" --baseline_file "*) exit "$FAKE_NEW";; *) exit "$FAKE_ALL";; esac;;
esac
exit 99
'''
CURL = r'''#!/bin/sh
echo "$@" >> "$STUB_DIR/curl.args"
out=""; while [ $# -gt 0 ]; do [ "$1" = "-o" ] && out="$2"; shift; done
if [ "$FAKE_BASELINE" = yes ]; then echo '{"findings":[]}' > "$out"; printf 200; else printf 404; fi
'''
def run(script, stage, *, baseline="no", new=0, all_=0, kind="builtin", policy="Some Policy", severity="", error="no", wrapper_rc=0, ref="feature/x", timeout="30"):
    d = tempfile.mkdtemp(); b = os.path.join(d, "bin"); os.mkdir(b)
    for n, c in (("java", JAVA), ("curl", CURL)):
        p = os.path.join(b, n); open(p, "w").write(c); os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    w = os.path.join(d, "w"); os.mkdir(w); open(os.path.join(w, "veracode-package.zip"), "w").write("x")
    if policy is not None: open(os.path.join(w, "veracode-policy.txt"), "w").write(policy + "\n")
    open(os.path.join(w, "job.sh"), "w").write(script)
    env = {"PATH": b + ":/usr/bin:/bin", "STUB_DIR": d, "FAKE_BASELINE": baseline, "FAKE_NEW": str(new), "FAKE_ALL": str(all_), "FAKE_POLICY_KIND": kind,
           "FAKE_SCAN_ERROR": error, "FAKE_WRAPPER_RC": str(wrapper_rc), "VERACODE_ROLLOUT_STAGE": stage, "VERACODE_COMPONENT_VERSION": ver,
           "VERACODE_APP_NAME": "demo-app", "VERACODE_ARTIFACT": "veracode-package.zip", "VERACODE_FAIL_ON_SEVERITY": severity,
           "VERACODE_BASELINE_MAP": "hotfix/*=main,*=develop", "VERACODE_BASELINE_PACKAGE": "veracode-baseline", "VERACODE_BASELINE_JOB": "veracode-baseline",
           "VERACODE_PIPELINE_TIMEOUT": "60", "VERACODE_SCAN_TIMEOUT": timeout, "VERACODE_API_KEY_ID": "stub-id", "VERACODE_API_KEY_SECRET": "stub-secret",
           "CI_API_V4_URL": "http://gitlab.invalid/api/v4", "CI_PROJECT_ID": "1", "CI_JOB_TOKEN": "stub", "CI_DEFAULT_BRANCH": "main", "CI_COMMIT_REF_NAME": ref,
           "CI_COMMIT_SHORT_SHA": "abc1234", "CI_PROJECT_PATH": "g/p", "CI_PROJECT_URL": "http://x/g/p"}
    r = subprocess.run(["sh", "job.sh"], cwd=w, env=env, capture_output=True, text=True)
    rd = lambda f: open(os.path.join(d, f)).read() if os.path.exists(os.path.join(d, f)) else ""
    return r.returncode, r.stdout + r.stderr, rd("java.args"), rd("curl.args")

if scripts:
    # Pipeline Scan gate: (stage, baseline, new, all) -> exit
    T = [("audit", "no", 0, 2, 0), ("audit", "yes", 1, 2, 0), ("audit", "yes", 0, 2, 0),
         ("warn", "no", 0, 2, 42), ("warn", "yes", 1, 2, 42), ("warn", "yes", 0, 2, 0), ("warn", "no", 0, 0, 0),
         ("block-new", "no", 0, 2, 42), ("block-new", "yes", 1, 2, 1), ("block-new", "yes", 0, 2, 0), ("block-new", "no", 0, 0, 0),
         ("block-policy", "no", 0, 2, 1), ("block-policy", "yes", 0, 2, 1), ("block-policy", "yes", 0, 0, 0)]
    for stage, bl, new, all_, want in T:
        rc, out, ja, ca = run(scripts[stage]["veracode-pipeline-scan"], stage, baseline=bl, new=new, all_=all_)
        check(f"gate {stage:<12} baseline={bl:<3} new={new} all={all_} -> exit {want}", rc == want, f"got {rc}: {out[-300:]}")
    rc, out, ja, ca = run(scripts["block-policy"]["veracode-pipeline-scan"], "block-policy", baseline="yes", all_=2)
    check("block-policy never passes --baseline_file and never fetches one", "--baseline_file" not in ja and ca == "")
    rc, out, ja, ca = run(scripts["block-new"]["veracode-pipeline-scan"], "block-new", baseline="yes", new=1, all_=2)
    check("block-new passes --baseline_file and built-in policy by name", "--baseline_file baseline.json" in ja and "--policy_name Some Policy" in ja and "--fail_on_severity" not in ja, ja)
    rc, out, ja, ca = run(scripts["block-new"]["veracode-pipeline-scan"], "block-new", baseline="yes", new=1, kind="custom")
    check("custom policy is downloaded and applied with --policy_file", "--policy_file .veracode-policy/Custom_Policy.json" in ja and "--policy_name" not in ja, ja)
    rc, out, ja, ca = run(scripts["block-new"]["veracode-pipeline-scan"], "block-new", baseline="yes", new=1, severity="Very High, High")
    check("fail_on_severity override replaces the policy", "--fail_on_severity Very High, High" in ja and "policy" not in ja, ja)
    for stage, want in (("audit", 42), ("warn", 42), ("block-new", 1), ("block-policy", 1)):
        rc, out, ja, ca = run(scripts[stage]["veracode-pipeline-scan"], stage, policy="")
        check(f"gate {stage:<12} no policy resolved, no override -> exit {want}, no scan without criteria", rc == want and "--file" not in ja, f"got {rc}")
        rc, out, ja, ca = run(scripts[stage]["veracode-pipeline-scan"], stage, error="yes")
        check(f"gate {stage:<12} scanner error -> exit {want}", rc == want, f"got {rc}")
    rc, out, ja, ca = run(scripts["warn"]["veracode-pipeline-scan"], "warn", ref="hotfix/1.2.1")
    check("baseline_map: hotfix/* is compared with main", "/veracode-baseline/main/baseline.json" in ca, ca)
    rc, out, ja, ca = run(scripts["warn"]["veracode-pipeline-scan"], "warn", ref="feature/abc")
    check("baseline_map: other branches are compared with develop", "/veracode-baseline/develop/baseline.json" in ca, ca)
    check("credentials never echoed by the gate script", "stub-secret" not in out and "stub-id" not in out)
    # Release-point policy scan: (stage, wrapper exit) -> exit
    for stage, wrc, want in [("audit", 0, 0), ("audit", 4, 0), ("audit", 1, 42), ("warn", 4, 42), ("warn", 1, 42), ("block-new", 4, 42), ("block-new", 1, 1),
                             ("block-policy", 0, 0), ("block-policy", 4, 1), ("block-policy", 1, 1)]:
        rc, out, ja, ca = run(scripts[stage]["veracode-policy-scan"], stage, wrapper_rc=wrc)
        check(f"release {stage:<12} wrapper exit {wrc} -> exit {want}", rc == want and "-createprofile false" in ja and "-scantimeout 30" in ja, f"got {rc}: {out[-200:]}")
done()
