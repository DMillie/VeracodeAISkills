# 06 Verification and report

Verification means reading the job logs and artifacts of the pipeline that ran on the MR, not
the pipeline's colour. Fill `templates/repo-summary.md`; every line names its evidence.

## Wait

`GET /projects/:id/merge_requests/:iid` → `head_pipeline.id`, then poll
`GET /projects/:id/pipelines/:pid` (`status`) and `GET /projects/:id/pipelines/:pid/jobs`
every 20–30 s. Budget: 10 minutes for Pipeline Scan + SCA + container on a small service. Do
not retry failed jobs blindly (rule 9).

## Per job: what counts as verified

| Job | Verified when | Evidence to quote | Not verified |
|---|---|---|---|
| packaging | archive listed in the log with the expected entries | listing line count, size | — |
| policy resolve | log names the policy and the application id | `Gate criteria: policy '<name>' assigned to application profile '<profile>'` | job orange (exit 42): profile missing or credentials; the gate then has no criteria |
| Pipeline Scan | `results.json` artifact exists; `scan_status` SUCCESS; counts by severity (`tools/pipeline_scan_summary.py results.json`); the `VERACODE GATE:` line | counts per severity, top CWEs, `stage=… criteria=… baseline=… matching=N` and the verdict line (AUDIT / WARNING / FAILED / PASSED) | job green with 0 findings on a non-trivial app → check packaging |
| baseline (after merge) | log says `Baseline published: package veracode-baseline/<slug>` | size, flaw count | job orange: package not published → `block-new` stays a warning |
| agent SCA | log shows `Scan ID`, the library counts (`Total Library Count`, or `Total Libraries` / `Direct Libraries` / `Transitive Libraries` depending on the package manager), `Vulnerable Libraries`, `Vulnerabilities` and a report URL | those lines | "SRCCLR_API_TOKEN is not set" or "There was a problem authenticating with Veracode SCA" → token problem: quote the log line, name the human fix (new CI-type agent token), keep the job, add the CLI directory scan as the interim SCA path, do not retry |
| CLI directory scan | table in `veracode-directory-scan.txt` | vulnerability rows by severity | — |
| container scan | table in `veracode-container-scan.txt` | image name, vulnerability rows by severity, policy result | — |
| policy scan | job waited and printed `VERACODE RELEASE GATE:` with the wrapper exit (0 pass, 4 did not pass), **and** the verdict was read back from the Platform (application `policy_compliance_status`, summary report) | scan name, build id, verdict, how the stage mapped it (audit: green; warn/block-new: orange; block-policy: red) | **submitted only** when the job returned without waiting: say "submitted, verdict not read" |
| sandbox scan | as policy scan, in the named sandbox | sandbox name, scan name | same |

Pre-scan read-back (the packaging proof for policy and sandbox scans): component >= 1.3.1 prints
`VERACODE PRE-SCAN` with the modules the Platform selected when the job waited. Otherwise read it
agent-side with the pinned API wrapper image, read-only actions `GetPreScanResults`, `GetBuildInfo`,
`GetFileList`, `DetailedReport` (`-appid`, `-buildid`, `-sandboxid` for sandboxes). Quote the
module names, their status and every fatal or warning issue. If the verdict is Did Not Pass, say
whether static flaws or SCA findings caused it.

Jobs that did not run on this MR (release-point jobs) are "configured, not run on this branch":
linted, not verified.

A job that ends orange (allowed failure, exit code 42) is the component's warning state: read
it, report it, do not retry it.

## Report (`repo-summary.md`)

0. Integration rung, component project and release, rollout stage chosen, recommended next stage
   and its condition.
1. Repository, branching model, placement table as implemented.
2. Change: files added/changed, lines added/deleted, MR URL, lint result.
3. Application profile: name, guid, created or existing.
4. Pipeline: id, URL, duration, per-job status with evidence from the table above.
5. Findings: Pipeline Scan counts by severity (and top issue types), SCA library and
   vulnerability counts (direct vs transitive if shown), container findings by severity.
6. Verified / submitted / not run: three explicit lists.
7. Next steps for the team: merge → baseline appears → propose `block-new` (one-line MR); policy scan runs at
   the release point; where results appear (job artifacts; the Platform application; the SCA
   workspace).
8. Timings: discovery → plan, plan → MR, MR → pipeline done.
