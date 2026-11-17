# Pipeline Scan

- `pipeline-scan.jar` flags (underscores): `--veracode_api_id/--veracode_api_key`, `--file`,
  `--fail_on_severity "Very High, High"`, `--baseline_file`, `--json_output_file`,
  `--filtered_json_output_file`, `--summary_output_file`, `--project_name/--project_url/--project_ref`,
  `--gl_vulnerability_generation true` (writes `veracode_gitlab_vulnerabilities.json`), `--timeout`
  minutes, `--development_stage {Development,Testing,Release}`, `--include`. **[live 2026-11-11, --help]**
- Exit code = number of flaws matching the fail criteria (1–200); 0 none; other values are
  errors. The CLI's `veracode static scan` exits 3 on matching flaws instead. **[2026-10]**
- Results are kept by Veracode for 24 hours only: keep `results.json` as a job artifact. **[2026-10]**
- Results never reach the Findings API or the application profile; compliance needs a policy scan.
- Severity in `results.json`: `findings[].severity` integer 5..0 (Very High..Informational),
  `cwe_id` string, `issue_type`, `files.source_file.{file,line}`. **[live 2026-11-11, see lab run 1]**
- `--fail_on_severity` takes English strings; the REST APIs take integers. Both are right.

Tags: **[live <date>]** observed in the lab on that date; **[2026-10, not re-verified]** carried over, check before relying on it.
