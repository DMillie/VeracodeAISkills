#!/usr/bin/env python3
"""Component 1.2.0 shapes: static off, per-application includes, pre-release sandbox tags, skipped
deploy branches, container needs. Dry-run on real refs of demo projects (skipped when absent)."""
import os
from _common import *
if not (TOKEN and URL and LINT_PROJECT): skip("set GITLAB_URL, GITLAB_TOKEN and LINT_PROJECT (a project the token can lint in)")
GROUP = os.environ.get("DEMO_GROUP", "demo")
V = component_version()
INC = "  - component: $CI_SERVER_FQDN/" + os.environ.get("COMPONENT_PROJECT", "platform/veracode-ci") + "/veracode@" + V + "\n    inputs:\n"
BASE = "stages: [build, test]\nveracode-package:\n  stage: build\n  script: [echo]\nbuild:\n  stage: build\n  script: [echo]\n"
def jobs(proj, ref, *input_sets):
    st, _ = api("GET", f"/projects/{GROUP}%2F{proj}")
    if st != 200: return None
    c = BASE + "include:\n" + "".join(INC + "".join(f"      {k}: {v}\n" for k, v in i.items()) for i in input_sets)
    out = lint(c, project=f"{GROUP}/{proj}", ref=ref)
    if out.get("valid") is False: return {"INVALID: %s" % out.get("errors")}
    return {j["name"].replace("veracode-", "") for j in out.get("jobs", []) if j["name"].startswith("veracode-") and j["name"] != "veracode-package"}
def expect(name, got, want):
    if got is None: print(f"  SKIPPED {name}: project not on this instance"); return
    check(f"{name}: {sorted(want) or 'no Veracode jobs'}", got == want, f"got {sorted(got)}")
A = {"app_name": "x"}
S3 = {"cli-directory-scan", "container-scan", "sca"}
expect("static off @ main", jobs("storefront-api", "main", dict(A, static_scan="false")), S3)
expect("static off @ feature", jobs("storefront-api", "feature/order-notes", dict(A, static_scan="false")), S3)
expect("gate_skip_branches @ main", jobs("storefront-api", "main", dict(A, gate_skip_branches="'^main$'")), S3 | {"policy-scan"})
expect("container_needs @ main", jobs("storefront-api", "main", dict(A, container_needs="[{job: build, artifacts: true}]")), S3 | {"baseline", "policy-scan"})
T = dict(A, release_branches="'^$'", release_tags="'^v\\d+\\.\\d+\\.\\d+$'", sandbox_tags="'^v.*-(rc|beta)'")
expect("pre-release tag -> sandbox only", jobs("pricing-engine", "v3.2.0-rc.1", T), {"sandbox-scan"})
expect("final tag -> policy scan only", jobs("pricing-engine", "v3.2.0", T), {"policy-scan"})
def app(a): return {"app_name": a, "job_suffix": f"'-{a}'", "source_dir": f"apps/{a}", "changes_paths": f"['apps/{a}/**/*']",
                    "release_branches": "'^$'", "release_tags": f"'^{a}\\/v'", "dockerfile": f"apps/{a}/Dockerfile"}
two = (app("console"), app("tracker-api"))
expect("two apps @ short-lived branch", jobs("fleet-platform", "feat/console-geofence-editor", *two),
       {f"{j}-{a}" for a in ("console", "tracker-api") for j in ("policy-resolve", "pipeline-scan", "sca", "cli-directory-scan")} | {"container-scan-tracker-api"})
expect("two apps @ console tag", jobs("fleet-platform", "console/v2.1.1", *two), {"policy-scan-console"})
expect("two apps @ tracker-api tag", jobs("fleet-platform", "tracker-api/v1.5.0", *two), {"policy-scan-tracker-api"})
done()
