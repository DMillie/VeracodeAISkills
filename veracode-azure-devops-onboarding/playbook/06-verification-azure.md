# 06 Azure: verification and report

Read `06-verification-and-report.md` for what "verified" means per scan. Use this file for the
Azure commands. Ignore the GitLab API calls and job names there. Where the two differ, this file wins.

## Wait and read

```
python3 tools/ado.py run-wait <run id>
python3 tools/ado.py run-log <run id> --step "Veracode: Pipeline Scan"
python3 tools/ado.py artifact <run id> veracode-results work/results-<run id>
python3 tools/pipeline_scan_summary.py work/results-<run id>/results.json
node tools/scan-check.js work/results-<run id>/results.json --module <deployable> --place <file>
```

`run-wait` (add `--timeout <seconds>` if needed) prints the result of every stage, job and step with its warnings. Budget: 10 minutes for
the package, Pipeline Scan and directory scan of a small service. If a step is still queued after
15 minutes the one agent is busy: say so, do not queue more.

Colours: `succeeded` all fine. `partiallySucceeded` (orange) = a step used `continueOnError` and logged a warning:
**read the warning, report it, do not retry**. `failed` = diagnose from `run-log`
(reference/troubleshooting.md); never re-run blind (rule 9). "Waiting for permission" = a person must click Permit
(00-integration-ladder-azure): stop.

## Which run shows what

- The run on your `veracode/...` branch (started by the push, or queued): package, placement ("none" on a branch that is not
  a scan ref), Pipeline Scan, directory scan, artifact. No upload.
- The run on the TARGET branch after the pull request is completed (`python3 tools/ado.py runs <repo> --branch <target>`):
  the placement step logs `kind=policy` or `kind=sandbox` and the scan name; the upload step runs. Read it too.
  Check the placement line: `python3 tools/ado.py run-log <run id> --step "Veracode: placement"`.

## Per step: verified when

| Step name (starts `Veracode:`) | Verified when | Evidence to quote |
|---|---|---|
| placement | the log line `Veracode placement for <ref>: kind=... sandbox=... scan name=...` matches the plan | that line |
| package | the log lists the archive with the expected files | file count, size |
| Pipeline Scan | `results.json` is in artifact `veracode-results`; `scan_status` SUCCESS; counts by severity; your expected places are in it (`scan-check.js`) | counts, top CWEs, the three places, `scan-check` verdict |
| directory scan | table in the artifact | rows by severity |
| policy or sandbox scan (`Veracode: policy or sandbox scan`, only on its refs) | the step ran and the log (`<kind>-scan.log` in the artifact, e.g. `policy-scan.log` or `sandbox-scan.log`; read its name from the artifact listing) names the scan and build id, **and** the verdict was read back from the Platform | scan name, build id, verdict. Not read back: write "submitted, verdict not read" |
| extension task (rung 3) | the Platform shows a scan newer than the run's start | scan name; never the step colour |

A step that did not run on this branch (release-ref-only) is "configured, not run on this branch".
A green run with 0 findings on a real application is a packaging problem until proven otherwise (playbook 04).
`ado.py` cannot read verdicts; if you have no read-only tool for the Platform, say "verdict not read".

## Report: `templates/repo-summary.md`

Fill every line with its evidence (run id, artifact file, log step). The three lists
"Verified", "Submitted, not verified", "Configured, not run" must be explicit.
The report ALWAYS states, in `Not covered`:

- Rollout stage `audit` only: no gate, no baseline, nothing blocks.
- Pull requests are not scanned until a person adds a build validation policy (if none exists).
- Container scan not covered.
- Which branches the team's trigger never runs.
- What is read from documentation and not run on Azure: see the facts file (`[ID~]` marks).

Next steps for the team: complete the pull request; merge into every other long-lived branch the
same way; add build validation; ask the platform team for stages beyond `audit` (not built).
