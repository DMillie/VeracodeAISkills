#!/usr/bin/env bash
# Static tier: seconds, no credentials, no network. Exit 0 only if nothing failed.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT="$(dirname "$(dirname "$HERE")")"; fail=0
step() { echo "=== $1"; shift; "$@"; rc=$?; [ $rc -eq 0 ] || { fail=1; echo "*** FAILED (exit $rc)"; }; }
step "shared files in step with their copies" python3 "$ROOT/tools/sync_shared.py" check
step "evidence register agrees with the skills" python3 "$ROOT/tools/evidence.py" check
for t in test_layout.py test_required_rules.py test_tools.py test_pins.py test_detect.py test_bitbucket.py test_azure.py; do step "$t" python3 "$HERE/$t"; done
[ $fail -eq 0 ] && echo "STATIC TIER PASSED" || echo "STATIC TIER FAILED"; exit $fail
