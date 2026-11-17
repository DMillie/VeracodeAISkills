#!/usr/bin/env bash
# GitLab tier: lints the component and its examples on a real GitLab and runs the gate scripts with stubs.
#   env: GITLAB_URL, GITLAB_TOKEN (never printed), LINT_PROJECT (any project the token can lint in),
#        COMPONENT_PROJECT (default platform/veracode-ci, must hold the released component)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; fail=0
for t in test_lint.py test_shapes.py test_rollout.py; do echo "=== $t"; python3 "$HERE/$t" || { fail=1; echo "*** $t FAILED"; }; done
[ $fail -eq 0 ] && echo "GITLAB TIER PASSED" || echo "GITLAB TIER FAILED"; exit $fail
