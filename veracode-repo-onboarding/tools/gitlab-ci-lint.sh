#!/usr/bin/env bash
# Lint one or more GitLab CI files against a GitLab instance's CI lint API (the real parser).
# `include: component:` and `include: project:` are resolved by the server with the token's
# permissions (so this also proves the token's user can read the shared component project);
# `include: local:` needs GITLAB_LINT_REF (a ref of <project> that holds the file).
#   usage: gitlab-ci-lint.sh <project path or id> <ci-file> [<ci-file> ...]
#   env:   GITLAB_URL (required), GITLAB_TOKEN (read access to the project)
#          GITLAB_LINT_REF (optional: ref whose files resolve `include: local:`; default = no ref,
#          so a standalone file must not include other files)
#          GITLAB_LINT_MERGED=<file> (optional: write the merged YAML the server returns, i.e. the
#          configuration after includes and component inputs were applied; one input file only)
#          GITLAB_LINT_PROBE=probe (append a trivial visible job: lints a file of hidden jobs only,
#          which the parser otherwise rejects with "should contain at least one visible job")
# Exit 0 if every file is valid, 1 otherwise. Prints errors and warnings; never prints the token.
set -euo pipefail
[ $# -ge 2 ] || { echo "usage: $0 <project> <ci-file> [...]" >&2; exit 2; }
URL="${GITLAB_URL:?set GITLAB_URL to your GitLab base URL}"; PROJECT="$1"; shift
: "${GITLAB_TOKEN:?set GITLAB_TOKEN}"
enc="$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$PROJECT")"
rc=0
for f in "$@"; do
  body="$(python3 - "$f" "${GITLAB_LINT_REF:-}" "" "${GITLAB_LINT_PROBE:-}" <<'PY'
import json, re, sys
content = open(sys.argv[1]).read()
if sys.argv[4] == "probe":   # a file of hidden jobs only: add one visible job so the parser accepts it
    content += "\nlint-probe:\n  script: [\"true\"]\n"
d = {"content": content, "include_jobs": True}
if sys.argv[2]: d["ref"] = sys.argv[2]; d["dry_run"] = True
print(json.dumps(d))
PY
)"
  out="$(curl -sS -X POST -H "PRIVATE-TOKEN: $GITLAB_TOKEN" -H "Content-Type: application/json" \
        --data-binary "$body" "$URL/api/v4/projects/$enc/ci/lint")"
  python3 - "$f" "$out" "${GITLAB_LINT_MERGED:-}" <<'PY' || rc=1
import json, sys
f, out = sys.argv[1], json.loads(sys.argv[2])
if sys.argv[3] and out.get("merged_yaml"): open(sys.argv[3], "w").write(out["merged_yaml"])
if "valid" not in out:
    print(f"{f}: lint API error: {out}"); sys.exit(1)
jobs = [j["name"] for j in out.get("jobs", [])]
print(f"{f}: valid={out['valid']} jobs={len(jobs)} errors={out['errors']} warnings={out['warnings']}")
if jobs: print("   ", ", ".join(jobs))
sys.exit(0 if out["valid"] else 1)
PY
done
exit $rc
