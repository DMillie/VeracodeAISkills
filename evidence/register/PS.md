# Evidence register: PS

| ID | Basis | Checked | Source or observation | Claim as written in the skill | File |
|---|---|---|---|---|---|
| PS-01 | lab | 2026-11-11 | --help | `pipeline-scan.jar` flags (underscores): `--veracode_api_id/--veracode_api_key`, `--file`, `--fail_on_severity "Very High, High"`, `--baseline_file`, `--json_output_file`, `--filtered_json_output_file`, `--summary_output_file`, `--project_name/--project_url/--project_ref`, `--gl_vulnerability_generation true` (writes `veracode_gitlab_vulnerabilities.json`), `--timeout` minutes, `--development_stage {Development,Testing,Release}`, `--include`. | `shared/reference/facts/pipeline-scan.md` |
| PS-02 | carried | 2026-10 | 2026-10 | Exit code = number of flaws matching the fail criteria (1–200); 0 none; other values are errors. The CLI's `veracode static scan` exits 3 on matching flaws instead. | `shared/reference/facts/pipeline-scan.md` |
| PS-03 | carried | 2026-10 | 2026-10 | Results are kept by Veracode for 24 hours only: keep `results.json` as a job artifact. | `shared/reference/facts/pipeline-scan.md` |
| PS-04 | lab | 2026-11-11 | see lab run 1 | Severity in `results.json`: `findings[].severity` integer 5..0 (Very High..Informational), `cwe_id` string, `issue_type`, `files.source_file.{file,line}`. | `shared/reference/facts/pipeline-scan.md` |
| PS-05 | lab | 2026-11-12 | observed in the lab | Pipeline Scan API: 6 scan submissions per minute per API user, then `HTTP Response 429`. One shared service account across many pipelines hits it; component >= 1.3.1 waits and retries. | `shared/reference/facts/pipeline-scan.md` |
| PS-06 | lab | 2026-11-12 | observed in the lab | A language Veracode Static does not analyse can still be ACCEPTED: a zipped Rust debug ELF gave `SCAN_STATUS SUCCESS`, one module, 0 findings. Zero findings on an unsupported language is no result, not a clean result. | `shared/reference/facts/pipeline-scan.md` |
