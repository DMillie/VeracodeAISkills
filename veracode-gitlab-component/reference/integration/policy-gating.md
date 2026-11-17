# 2. Policy-driven gating: pipeline-scan.jar and Veracode CLI

Source for the jar table: https://docs.veracode.com/r/Pipeline_Scan_parameters (page last updated Feb 24, 2026).

| Parameter | What the docs say | Marker |
|---|---|---|
| `--request_policy` / `-rp` | Downloads the named policy as a file into the working directory. No scan runs. Needed for custom policies. Docs advise not downloading on every build. | docs only (read 2026-11-12) |
| `--policy_file` / `-pf` | Applies a local policy file (the one produced by `--request_policy`) to the results. | docs only (read 2026-11-12) |
| `--policy_name` / `-pn` | Applies a policy by name; "You can only use this parameter with a default policy" (i.e. built-in policies). | docs only (read 2026-11-12) |
| `--fail_on_severity` / `-fs` | Comma-separated severities. Default is all five severities. | docs only (read 2026-11-12) |
| `--fail_on_cwe` / `-fc` | Comma-separated CWE IDs. Default all CWEs. If used alone, the default severity list still applies. | docs only (read 2026-11-12) |
| `--baseline_file` / `-bf` | Filters out flaws present in the baseline; only new flaws are reported. | docs only (read 2026-11-12) |
| `--app_id` / `-aid` | Exists. Application profile ID for the scan. | docs only (read 2026-11-12) |
| `--development_stage` / `-ds` | Exists. Case-sensitive: `Development`, `Testing`, `Release`. | docs only (read 2026-11-12) |
| Output | `--json_output_file` (default `results.json`), `--filtered_json_output_file` (default `filtered_results.json`, must differ), `--summary_output`, `--issue_details`, `--gl_issue_generation`, `--gl_vulnerability_generation`. | docs only (read 2026-11-12) |
| Other | `--timeout` (default and max 60 min), `--include`, `--project_name/_url/_ref`, `--emit_stack_dump`, `--veracode_profile`. | docs only (read 2026-11-12) |
| Actual `--help` output of the pinned jar | - | verified locally 2026-11-12 (`reference/integration/verified-locally.md`) |

| Fact | Source | Marker |
|---|---|---|
| In the GitLab example, `--policy_name` "replaces the --fail_on_severity and --fail_on_cwe parameters". | https://docs.veracode.com/r/Example_code_for_GitLab | docs only (read 2026-11-12) |
| Policy + baseline: define criteria by severity/CWE or by `--policy_file`/`--policy_name`, add `-bf`; the stage fails only for flaws matching the criteria that are not in the baseline; passes if none match or all are in the baseline. | https://docs.veracode.com/r/r_pipeline_scan_examples | docs only (read 2026-11-12) |
| Policy rule types honoured: findings by CWE ID, by CWE category, by severity. Grace periods, scan frequency and evaluation time frames are not considered. | https://docs.veracode.com/r/Configure_Pipeline_Scan_setings | docs only (read 2026-11-12) |
| Baseline can only be produced by Pipeline Scan (a renamed `results.json`), not from the Platform; docs advise versioning it next to the app. Pipeline Scan has no mitigations or flaw matching. | https://docs.veracode.com/r/Pipeline_Scan | docs only (read 2026-11-12) |
| Exit/status codes: 0 = no flaws; 1-200 = number of flaws (capped at 200); -1/255 = failure (network, credentials, other); -2/254 = default 60-min timeout; -3/253 = `--timeout` exceeded. | https://docs.veracode.com/r/Pipeline_Scan (Status codes) | docs only (read 2026-11-12) |
| Rate/time limits: six pipeline scans per minute per user (HTTP 429 beyond that); 60 minutes max per scan. | https://docs.veracode.com/r/Pipeline_Scan | docs only (read 2026-11-12) |
| Whether a combination of `--policy_file` and `--fail_on_severity` is merged or one wins | - | not verified locally (the jar help lists `-pn` and `-pf` as mutually exclusive; the combination with `-fs` was not run) |

Veracode CLI equivalents (https://docs.veracode.com/r/veracode_static_scan, last updated Feb 4, 2026):

| Fact | Source | Marker |
|---|---|---|
| `veracode static scan <file>` runs a Pipeline Scan. Flags: `--baseline-file`, `--fail-on-cwe`, `--fail-on-severity`, `--policy-file`, `--results-file` (default `./results.json`), `--summary-output`, `--include`, `--app-id`, `--development-stage`, `--project-name/-ref/-url`, `--gl-issue-generation`, `--gl-vulnerability-generation`. | https://docs.veracode.com/r/veracode_static_scan | docs only (read 2026-11-12) |
| No `--policy-name` flag is documented for `static scan`. Policy files come from `veracode policy get "<policy_name>"` (built-in or custom; name must not contain `/`, `\` or `+`). | https://docs.veracode.com/r/veracode_policy | docs only (read 2026-11-12) |
| Exit codes: 0 success; 1 generic error; 2 parser error; 3 scan completed but "did not pass policy"; 4-7 packaging; 125-130 system. Note this differs from the jar (flaw count). | https://docs.veracode.com/r/CLI_exit_codes | docs only (read 2026-11-12) |
| CLI v2.53.0 release notes mention a new `veracode scan static` command; its flags were not reviewed. | https://docs.veracode.com/updates/r/Veracode_CLI_Updates | docs only (read 2026-11-12); details not confirmed |
| Actual CLI `--help` for the pinned version | - | not verified locally (the component does not use `veracode static scan`) |

Index and reading guide: `reference/integration-options.md`.
