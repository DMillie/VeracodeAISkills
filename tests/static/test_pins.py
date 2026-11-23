#!/usr/bin/env python3
"""(b) Nothing floats: no `:latest`, no remote script piped into a shell, every image of the
component pinned by tag AND digest, component include pinned to an exact semantic version."""
import glob, os, re
from _common import *
files = [TEMPLATE] + EXAMPLES + glob.glob(os.path.join(PACK, "templates/gitlab/component/tools/*"))
for f in files:
    rel = os.path.relpath(f, PACK); body = open(f).read()
    if f in EXAMPLES: body = body.split("Veracode security scanning (added by onboarding)", 1)[1]   # only what onboarding added; the team's own jobs are theirs
    code = [l for l in body.splitlines() if not l.lstrip().startswith("#")]
    text = "\n".join(code)
    check(f"{rel}: no :latest image", not re.search(r"(?m)image:.*:latest|[\w/.-]+:latest\b", "\n".join(l for l in code if "LATEST_VERSION" not in l)), "latest tag found")
    check(f"{rel}: no download piped into a shell", not re.search(r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b", text), "curl|sh found")
t = open(TEMPLATE).read()
defaults = dict(re.findall(r"(?m)^    (\w+_image):\n(?:      description:.*\n)?      default: '?([^'\n]+)'?", t))
for k in ("pipeline_scan_image", "api_wrapper_image", "cli_image", "docker_image", "dind_image"):
    v = defaults.get(k, ""); check(f"template: {k} pinned tag@sha256 ({v.split('@')[0]})", bool(re.fullmatch(r"[\w/.-]+:[\w.-]*\d[\w.-]*@sha256:[0-9a-f]{64}", v)), v)
for k in ("cli_sha256", "sca_agent_sha256_glibc", "sca_agent_sha256_musl"):
    m = re.search(rf"(?m)^    {k}:\n(?:      description:.*\n)?      default: '([0-9a-f]{{64}})'", t); check(f"template: {k} is a SHA-256", bool(m))
for k in ("cli_version", "sca_agent_version"):
    m = re.search(rf"(?m)^    {k}:\n      default: '(\d+\.\d+\.\d+)'", t); check(f"template: {k} is an exact version", bool(m))
check("template: SCA agent verified before execution", "sha256sum -c" in t and "ci.sh" not in "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("#")))
for f in EXAMPLES:
    inc = re.findall(r"component:\s*(\S+)", open(f).read())
    check(f"{os.path.basename(f)}: component pinned to exact x.y.z", len(inc) == 1 and bool(re.search(r"@\d+\.\d+\.\d+$", inc[0])), str(inc))
    check(f"{os.path.basename(f)}: no hidden-job copy / local include", "local:" not in open(f).read() and ".veracode-" not in open(f).read())
done()
