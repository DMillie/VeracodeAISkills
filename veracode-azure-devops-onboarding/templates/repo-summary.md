# Veracode onboarding summary: <project>/<repository> (Azure DevOps)

Date: <YYYY-MM-DD>. Agent: <name>. Pull requests: <urls or ids>. Runs: <ids>.

## Integration

- Rung <N>: <template repository veracode-pipelines at tag ... / copied file / extension task>; reason <...>.
- Rollout stage `audit`. Re-run check: `ado.py detect` -> <result>.

## Verified (ran, evidence read)

| Step | Run / artifact | Evidence |
|---|---|---|
| package | run <id> | <files, size> |
| Pipeline Scan | `veracode-results/results.json` | <N findings: by severity; top CWEs; expected places found; scan-check verdict> |
| directory scan | artifact | <rows by severity> |

## Submitted, not verified

| Scan | What happened | What is missing |
|---|---|---|
| policy scan | <build id, uploaded> | verdict not read |

## Configured, not run on this branch

- <step>: runs on <ref>.

## Not covered

- Rollout stage audit only: no gate, no baseline.
- Pull requests not scanned until a build validation policy exists: <exists / does not>.
- Container scan; branches the trigger never runs: <...>.
- Read from documentation, not run on Azure: <list from the facts file>.

## Change

- Files: <path> (+N / -0). Lint: <OK, steps listed>. Profile <name>, <created/existing>.

## Next steps for the team

1. Review and complete the pull request; repeat for <other long-lived branches>.
2. Add build validation on <branch> to scan pull requests (project setting).
3. Open questions <...>.
