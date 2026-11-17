# Veracode onboarding summary: <group/project>

Date: <YYYY-MM-DD>. Agent: <name>. MR: <url>. Pipeline: <url>.

## Integration

- Rung <2>: `<component path>@<X.Y.Z>` included by reference (<include form>); reason: <…>.
- Rollout stage: `<audit>`. Gate criteria: policy `<name>` of application `<profile>` <or override>.
- Recommended next stage: `<block-new>` when <the target branch has published a baseline>; a one-line change.
- Re-run check: `tools/detect_integration.py` → <nothing to do / upgrade to X.Y.Z proposed in MR …>.

## Verified (ran on this MR, evidence read)

| Scan | Job | Status | Evidence |
|---|---|---|---|
| Policy resolve | `veracode-policy-resolve` | <ok / warning> | policy `<name>`, application id <…> |
| Pipeline Scan | `veracode-pipeline-scan` | <passed / audit / warning / failed> | `results.json`: <N> findings: Very High <a>, High <b>, Medium <c>, Low <d>; top: <CWE list>; gate line: stage=<…> criteria=<…> baseline=<yes/no> matching=<n> |
| Agent SCA | `veracode-sca` | <ok> | log: Total Library Count <n>, Vulnerable Libraries <v>, Vulnerabilities <k>; Scan ID <…>; report URL <…> |
| Container scan | `veracode-container-scan` | <ok> | image `<name:tag>`: <rows by severity>; policy <…> |
| CLI directory scan | `veracode-cli-directory-scan` | <ok / not configured> | <rows by severity> |

## Submitted, not verified

| Scan | Job | What happened | What is missing |
|---|---|---|---|
| Policy scan | `veracode-policy-scan` | <upload accepted, build id …> | verdict not read (timeout 0) |

## Configured, not run on this branch (release point only)

- <job>: runs on <branch/tag>; linted <date>.

## Change

- Files: `.gitlab-ci.yml` (+N / −0): component include + inputs <+ packaging job>. No other file.
- Lint: valid, <n> jobs, warnings <none>.
- Application profile: `<name>`, guid `<…>`, <created / existing>.
- Placement as implemented: <table or reference to the plan>.

## Timings

| Phase | Duration |
|---|---|
| Discovery → plan | |
| Plan → MR opened | |
| MR pipeline (queued → done) | |

## Next steps for the team

1. Review and merge the MR. The first `<target>` pipeline publishes the baseline; then change
   `rollout_stage` to `block-new` (one line) so MRs fail only on new flaws that violate the policy.
2. The policy scan runs at <release point>; the verdict appears on the Platform under `<profile>`.
3. SCA results: SCA workspace project `<…>`; Pipeline Scan results: job artifacts (24 h on Veracode's side).
4. Open questions: <…>.
