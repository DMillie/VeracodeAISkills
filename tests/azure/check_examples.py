#!/usr/bin/env python3
"""Offline checks of templates/azure/examples (no credentials, no network).

  check_examples.py [templates/azure dir]

For every <name>.before.yml / <name>.after.yml pair:
  - the after file keeps EVERY non-blank line of the before file, in order (additions only);
  - it pins the template repository to an exact tag (ref: refs/tags/vX.Y.Z), never a branch;
  - it calls veracode-steps.yml@veracode with an appProfile, and names the variable group veracode;
  - every template call has a distinct artifactName when there is more than one.
Also: templates/azure/veracode-steps.yml is the released file in
platform/veracode-pipelines-ado/ (comment lines aside) when that repository is present (lab checkout only)."""
import os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "..", "shared", "templates", "azure")
ex = os.path.join(root, "examples"); fails = []

def nonblank(t): return [l.rstrip() for l in t.splitlines() if l.strip()]
def fail(m): fails.append(m); print("FAIL", m)

pairs = sorted(f[:-len(".before.yml")] for f in os.listdir(ex) if f.endswith(".before.yml"))
if len(pairs) < 3: fail(f"expected at least 3 examples, found {len(pairs)}")
for name in pairs:
    b, a = os.path.join(ex, name + ".before.yml"), os.path.join(ex, name + ".after.yml")
    if not os.path.isfile(a): fail(f"{name}: no .after.yml"); continue
    before, after = nonblank(open(b).read()), open(a).read(); al = nonblank(after); i = 0
    for line in al:
        if i < len(before) and line == before[i]: i += 1
    if i < len(before): fail(f"{name}: line {i+1} of the before file is not kept (additions only): {before[i].strip()[:80]!r}")
    tag = re.search(r"(?m)^\s*ref:\s*refs/tags/v\d+\.\d+\.\d+\s*$", after)
    if not tag: fail(f"{name}: template not pinned to an exact tag (ref: refs/tags/vX.Y.Z)")
    if re.search(r"(?m)^\s*ref:\s*refs/heads/", after): fail(f"{name}: a repository resource points at a branch")
    if not re.search(r"(?m)^\s*name:\s*veracode-pipelines\s*$", after): fail(f"{name}: repository veracode-pipelines not declared")
    calls = len(re.findall(r"(?m)^\s*-\s*template:\s*veracode-steps\.yml@veracode\s*$", after))
    profiles = re.findall(r"(?m)^\s*appProfile:\s*(\S+)", after); arts = re.findall(r"(?m)^\s*artifactName:\s*(\S+)", after)
    if calls < 1 or len(profiles) != calls: fail(f"{name}: {calls} template call(s) but {len(profiles)} appProfile line(s)")
    if calls > 1 and (len(arts) != calls or len(set(arts)) != calls): fail(f"{name}: several template calls need a distinct artifactName each")
    if calls > 1 and len(set(profiles)) != calls: fail(f"{name}: two calls with the same appProfile")
    if not re.search(r"(?m)^\s*-\s*group:\s*veracode\s*$", after): fail(f"{name}: variable group veracode not referenced")
    if re.search(r"VERACODE_API_KEY_(ID|SECRET)\s*[:=]\s*['\"]?[0-9a-f]{16,}", after): fail(f"{name}: looks like a credential value")
    print(f"ok   {name}: additions only, {calls} template call(s), pinned")

rel = os.path.join(here, "..", "..", "..", "..", "platform", "veracode-pipelines-ado", "veracode-steps.yml")
mine = os.path.join(root, "veracode-steps.yml")
if not os.path.isfile(mine): fail("templates/azure/veracode-steps.yml missing")
elif os.path.isfile(rel):
    code = lambda f: [l for l in open(f).read().splitlines() if not l.lstrip().startswith("#")]   # the copy may differ in comment lines only (a lab profile name in an example)
    if code(rel) != code(mine): fail("templates/azure/veracode-steps.yml differs from platform/veracode-pipelines-ado/veracode-steps.yml")
    else: print("ok   veracode-steps.yml identical to the released file")
else: print("skip released-file comparison (platform/veracode-pipelines-ado not in this checkout)")
print("AZURE OFFLINE CHECK", "FAILED" if fails else "PASSED"); sys.exit(1 if fails else 0)
