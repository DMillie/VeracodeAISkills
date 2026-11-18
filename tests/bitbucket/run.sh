#!/usr/bin/env bash
# Bitbucket tier, local half: runs the package, Pipeline Scan and report step scripts of an example
# in their pinned images against a source tree, the way a Bitbucket step would (one container per
# step, files handed on in the working directory). It does NOT run anything on Bitbucket and does
# not run the policy scan step. One Pipeline Scan is used (limit: 6 per minute).
#   usage: run.sh <example.yml> <source dir> <work dir> [expected findings]
# Needs docker and VERACODE_API_KEY_ID / VERACODE_API_KEY_SECRET in the environment.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; YML="$(readlink -f "$1")"; SRC="$(readlink -f "$2")"; W="$3"; WANT="${4:-}"
: "${VERACODE_API_KEY_ID:?not set}" "${VERACODE_API_KEY_SECRET:?not set}"
mkdir -p "$W"; W="$(readlink -f "$W")"; cp -a "$SRC"/. "$W"/; chmod -R a+rwX "$W"; fail=0
step() { # <anchor> [docker args]
  local a="$1"; shift; local img; img="$(python3 "$HERE/extract_step.py" "$YML" "$a" image)"
  python3 "$HERE/extract_step.py" "$YML" "$a" script > "$W/.step-$a.sh"
  echo "=== $a  ($img)"; docker run --rm "$@" -v "$W":/w -w /w "$img" sh "/w/.step-$a.sh"; local rc=$?
  echo "--- $a exit $rc"; [ $rc -eq 0 ] || fail=1
}
step veracode-package
step veracode-pipeline-scan -e VERACODE_API_KEY_ID -e VERACODE_API_KEY_SECRET
step veracode-report
docker run --rm -v "$W":/w alpine:3.24.4 chown -R "$(id -u):$(id -g)" /w
n="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["findings"]))' "$W/results.json" 2>/dev/null || echo none)"
echo "findings: $n"; python3 -c 'import json,sys; r=json.load(open(sys.argv[1]+"/veracode-report.json")); a=json.load(open(sys.argv[1]+"/veracode-annotations.json")); print("report data:", [(d["title"], d["value"]) for d in r["data"]], "annotations:", len(a), "first:", a[0] if a else None)' "$W" || fail=1
[ -z "$WANT" ] || [ "$n" = "$WANT" ] || { echo "*** expected $WANT findings"; fail=1; }
[ $fail -eq 0 ] && echo "BITBUCKET LOCAL STEPS PASSED (not run on Bitbucket)" || echo "BITBUCKET LOCAL STEPS FAILED"; exit $fail
