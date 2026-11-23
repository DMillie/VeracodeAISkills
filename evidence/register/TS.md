# Evidence register: TS

| ID | Basis | Checked | Source or observation | Claim as written in the skill | File |
|---|---|---|---|---|---|
| TS-01 | lab | 2026-11-12 | observed in the lab | Pipeline not created / lint: `Component '…/veracode@X' - project does not exist or you don't have sufficient permissions` (or `Project … not found or access denied` for `include: project`) | `shared/reference/troubleshooting.md` |
| TS-02 | lab | 2026-11-12 | observed in the lab | Lint: `Component '…@1.0' - content not found` / `@~latest` not found | `shared/reference/troubleshooting.md` |
| TS-03 | lab | 2026-11-12 | observed in the lab | After adding the Veracode include the team's own included jobs disappeared, or lint says `unknown keys in extends` for an existing job | `shared/reference/troubleshooting.md` |
| TS-04 | lab | 2026-11-12 | component pre-release | A release-point job (`veracode-policy-scan`) ran on a feature branch | `shared/reference/troubleshooting.md` |
| TS-05 | lab | 2026-11-12 | observed in the lab | Pipeline Scan: `Builtin policies cannot be downloaded` in `.veracode-policy/request.log` | `shared/reference/troubleshooting.md` |
| TS-06 | lab | 2026-11-12 | component 1.0.0 | The team's later stages wait many minutes on main | `shared/reference/troubleshooting.md` |
| TS-07 | lab | 2026-11-11 | observed in the lab | Pipeline Scan: `Either the file 'results.json' does not have the correct file permissions` or `FileNotFoundException … (Permission denied)`, intermittently | `shared/reference/troubleshooting.md` |
| TS-08 | lab | 2026-11-11 | observed in the lab | SCA agent: `There was a problem authenticating with Veracode SCA. Please double check your Veracode SCA agent credentials or the value of the env variable "SRCCLR_API_TOKEN".` (after ~2 min of silence) | `shared/reference/troubleshooting.md` |
| TS-09 | carried | 2026-10 | 2026-10 | Upload and Scan stuck at `Pre-Scan Success` after a fatal pre-scan | `shared/reference/troubleshooting.md` |
| TS-10 | lab | 2026-11-11 | observed in the lab | CLI directory scan lists Go modules (`github.com/docker/docker`, `golang.org/x/net`, `stdlib`) in a non-Go repo | `shared/reference/troubleshooting.md` |
| TS-11 | lab | 2026-11-11 | observed in the lab | Baseline job: `could not publish the baseline package: HTTP 000` / `curl-error`, and MR jobs report `package: HTTP 000` | `shared/reference/troubleshooting.md` |
| TS-12 | lab | 2026-11-11 | observed in the lab | MR job says "No baseline for 'main' yet" although `veracode-baseline` ran green on main | `shared/reference/troubleshooting.md` |
| TS-13 | lab | 2026-11-11 | observed in the lab | Team's own later-stage job skipped after a Veracode job failed | `shared/reference/troubleshooting.md` |
| TS-14 | lab | 2026-11-12 | observed in the lab | Pipeline Scan: `PIPELINE-SCAN ERROR: CREATE FAILURE: HTTP Response 429: Too many requests ... 6 scans per minute` | `shared/reference/troubleshooting.md` |
| TS-15 | lab | 2026-11-12 | observed in the lab | Pipeline Scan: `No files found for scanning`, exit 255 | `shared/reference/troubleshooting.md` |
| TS-16 | lab | 2026-11-12 | observed in the lab | Pipeline Scan green, `SUCCESS`, 0 or very few findings on a real application | `shared/reference/troubleshooting.md` |
| TS-17 | lab | 2026-11-12 | observed in the lab | Policy scan Did Not Pass although the static findings do not violate the policy | `shared/reference/troubleshooting.md` |
| TS-18 | lab | 2026-11-12 | CLI 2.40.0 download returned 404 from tools.veracode.com | CLI or agent download 404 for a pinned version | `shared/reference/troubleshooting.md` |
