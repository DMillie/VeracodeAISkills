#!/usr/bin/env python3
"""(a) Lint the component and every example with the GitLab CI lint API (the real parser, which
resolves the component include with the token's permissions), and check the pack's copy of the
component equals the released tag on the instance."""
import os, re, urllib.parse
from _common import *
if not (TOKEN and URL and LINT_PROJECT): skip("set GITLAB_URL, GITLAB_TOKEN and LINT_PROJECT (a project the token can lint in)")
ver = component_version(); comp = urllib.parse.quote(COMPONENT_PROJECT, safe="")
st, raw = api("GET", f"/projects/{comp}/repository/files/{urllib.parse.quote('templates/veracode/template.yml', safe='')}?ref={ver}")
import base64
released = base64.b64decode(raw.get("content", "")).decode() if st == 200 else ""
check(f"{COMPONENT_PROJECT} has tag {ver} with the component file", st == 200, f"HTTP {st}")
check(f"pack copy of template.yml == released {ver}", released == open(TEMPLATE).read(), "differs: release a new version or sync the pack copy")
minimal = "include:\n  - {form}\n    inputs:\n      app_name: lint-probe\n      sca_image: python:3.11\nveracode-package:\n  script: ['true']\n"
forms = {"component": f"component: $CI_SERVER_FQDN/{COMPONENT_PROJECT}/veracode@{ver}",
         "project/ref/file": f"project: {COMPONENT_PROJECT}\n    ref: '{ver}'\n    file: templates/veracode/template.yml"}
for name, form in forms.items():
    out = lint(minimal.format(form=form)); jobs = [j["name"] for j in out.get("jobs", [])]
    check(f"include form {name}@{ver}: valid, 9 jobs, no warnings", out.get("valid") and len(jobs) == 9 and not out.get("warnings"), str(out.get("errors")) + str(out.get("warnings")))
if "release_stage" in open(TEMPLATE).read():
    out = lint("stages: [build, test]\n" + minimal.format(form=forms["component"])); st = {j["name"]: j["stage"] for j in out.get("jobs", [])}
    check("policy and sandbox scans run in .post by default (never delay the project's stages)", st.get("veracode-policy-scan") == ".post" and st.get("veracode-sandbox-scan") == ".post" and st.get("veracode-pipeline-scan") == "test", str(st))
out = lint(f"include:\n  - local: templates/veracode/template.yml\n    inputs:\n      app_name: lint-probe\nveracode-package:\n  script: ['true']\n", project=COMPONENT_PROJECT, ref=ver)
check(f"include form local copy (linted inside {COMPONENT_PROJECT}@{ver}): valid", out.get("valid") and not out.get("warnings"), str(out.get("errors")))
out = lint(minimal.format(form=forms["component"]).replace("app_name: lint-probe", "app_name: x\n      rollout_stage: strict"))
check("unknown rollout_stage value is rejected by the parser", not out.get("valid"), "accepted")
out = lint("include:\n  - " + forms["component"] + "\nveracode-package:\n  script: ['true']\n")
check("missing app_name is accepted since 1.3.0 (needed for static_scan false; veracode-policy-resolve warns at run time when static is on)", out.get("valid") is True, "rejected")
for f in EXAMPLES:
    out = lint(open(f).read()); jobs = [j["name"] for j in out.get("jobs", [])]
    vj = [j for j in jobs if j.startswith("veracode-")]
    check(f"{os.path.basename(f)}: valid, {len(jobs)} jobs ({len(vj)} veracode), no warnings", out.get("valid") and not out.get("warnings") and len(vj) >= 8, str(out.get("errors")) + str(out.get("warnings")))
done()
