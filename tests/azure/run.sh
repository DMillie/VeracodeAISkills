#!/usr/bin/env bash
# Azure DevOps tier.
#   offline (always):  every example's "after" keeps every non-blank line of its "before" and pins the template by tag
#   online  (only when AZURE_DEVOPS_ORG and AZURE_DEVOPS_PAT are set): every "after" expands in the pipeline preview API
#                      of a real project (ado.py validate). The pinned tag must exist in repository veracode-pipelines.
#   env: AZURE_DEVOPS_ORG, AZURE_DEVOPS_PAT (never printed), ADO_PROJECT (default veracode-demo)
#        ADO_TARGETS: "<example>=<repo>:<pipeline>:<branch> ..." default below: the lab's sample repositories
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT="$HERE/../.."; fail=0
python3 "$HERE/check_examples.py" "$ROOT/shared/templates/azure" || fail=1
if [ -n "${AZURE_DEVOPS_ORG:-}" ] && [ -n "${AZURE_DEVOPS_PAT:-}" ]; then
  P="${ADO_PROJECT:-veracode-demo}"
  TARGETS="${ADO_TARGETS:-trunk-typescript=parcel-tracker:parcel-tracker:main git-flow-java=payments-service:payments-service:develop monorepo-two-apps=parcel-tracker:parcel-tracker:main}"
  for t in $TARGETS; do
    ex="${t%%=*}"; IFS=: read -r repo pipe branch <<<"${t#*=}"
    echo "=== validate $ex on $repo/$pipe@$branch"
    out="$(python3 "$ROOT/shared/tools/ado.py" --project "$P" validate "$repo" "$pipe" "$branch" --file "$ROOT/shared/templates/azure/examples/$ex.after.yml" 2>&1)"; rc=$?
    echo "$out" | head -40
    [ $rc -eq 0 ] && echo "$out" | grep -q "Veracode: Pipeline Scan" || { echo "*** $ex FAILED"; fail=1; }
  done
else echo "skip online tier (set AZURE_DEVOPS_ORG and AZURE_DEVOPS_PAT)"; fi
[ $fail -eq 0 ] && echo "AZURE TIER PASSED" || echo "AZURE TIER FAILED"; exit $fail
