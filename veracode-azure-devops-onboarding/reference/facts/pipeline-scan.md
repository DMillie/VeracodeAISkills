# Pipeline Scan

- `pipeline-scan.jar` flags (underscores): `--veracode_api_id/--veracode_api_key`, `--file`,
  `--fail_on_severity "Very High, High"`, `--baseline_file`, `--json_output_file`,
  `--filtered_json_output_file`, `--summary_output_file`, `--project_name/--project_url/--project_ref`,
  `--gl_vulnerability_generation true` (writes `veracode_gitlab_vulnerabilities.json`), `--timeout`
  minutes, `--development_stage {Development,Testing,Release}`, `--include`. [PS-01]
- Exit code = number of flaws matching the fail criteria (1–200); 0 none; other values are
  errors. The CLI's `veracode static scan` exits 3 on matching flaws instead. [PS-02?]
- Results are kept by Veracode for 24 hours only: keep `results.json` as a job artifact. [PS-03?]
- Results never reach the Findings API or the application profile; compliance needs a policy scan.
- `results.json`: `findings[].severity` integer 5..0 (Very High..Informational), `cwe_id` string,
  `issue_type`, `files.source_file.{file,line}`. [PS-04]
- `--fail_on_severity` takes English strings; the REST APIs take integers. Both are right.
- Limit: 6 scan submissions per minute per API user, then `HTTP Response 429`. One service
  account shared by many pipelines hits it; component >= 1.3.1 waits and retries. [PS-05]
- An unsupported language can still be ACCEPTED (`SCAN_STATUS SUCCESS`, one module, 0 findings).
  Zero findings on an unsupported language is no result, not a clean result. [PS-06]

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
