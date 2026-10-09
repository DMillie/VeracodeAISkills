# CI/CD integrations

**Traps in this file:** converting results to SARIF does **not** publish them —
a separate upload step does · plugin credentials are **HMAC**, never OAuth ·
`fail_on_severity` takes English strings while the REST API takes integers ·
fork PRs cannot write to the GitHub Security tab.

All version tags are `[v: 2026-09-15]`. Tags rot — verify before pinning, or tell
the user you are quoting a snapshot.

---

## Choosing the scan

| Trigger | Scan | Why |
|---|---|---|
| `pull_request` | **Pipeline Scan** | Minutes, ephemeral, local JSON. Does not touch the profile. |
| `push` to main / release | **Policy (Upload & Scan)** | Authoritative, updates the profile, drives compliance and the Findings API. |

A PR gate on Upload & Scan is too slow and pollutes the profile. A compliance
report built on Pipeline Scan finds nothing, because pipeline results never reach
the Findings API.

---

# GitHub Actions

## The three-step SARIF chain

Commonly confused, so state it explicitly:

1. `veracode/Veracode-pipeline-scan-action` — runs the scan, **breaks the build**
2. `veracode/veracode-pipeline-scan-results-to-sarif` — **converts** JSON → SARIF.
   Publishes nothing.
3. `github/codeql-action/upload-sarif` — **publishes** to the Security tab.
   Requires `permissions: security-events: write`.

Omit step 3 and nothing appears, with no error.

```yaml
name: Veracode PR scan

on:
  pull_request:
    branches: [ main ]

permissions:
  contents: read
  security-events: write          # required for the Security tab

jobs:
  pipeline_scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Veracode scans built artifacts, not source.
      - name: Build
        run: mvn -B package --file pom.xml

      - name: Veracode Pipeline Scan
        uses: veracode/Veracode-pipeline-scan-action@v1.0.23   # [v: 2026-09-15]
        with:
          vid: ${{ secrets.VERACODE_API_KEY_ID }}      # HMAC id, NOT an OAuth client id
          vkey: ${{ secrets.VERACODE_API_KEY_SECRET }}
          file: 'target/app.jar'
          fail_build: true
          fail_on_severity: 'Very High, High'          # English strings here
          baseline_file: 'baseline.json'               # see pipeline-scan.md

      - name: Convert results to SARIF
        if: always()                                   # previous step failed on purpose
        uses: veracode/veracode-pipeline-scan-results-to-sarif@v2.0.5   # [v: 2026-09-15]
        with:
          scan-type: pipeline
          results-json: filtered_results.json
          output-results-sarif: veracode-results.sarif
          githubToken: ${{ secrets.GITHUB_TOKEN }}
          ref: ${{ github.ref }}
          commitSHA: ${{ github.sha }}
          # source-base-path-1: "^com/example:src/main/java/com/example"

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: veracode-results.sarif
```

### Gotchas

- **SARIF action input names changed across majors.** v1.x used
  `pipeline-results-json` with `repo_owner`/`repo_name`; v2.x uses `scan-type` +
  `results-json` + `githubToken`/`ref`/`commitSHA`. If the user pins a different
  tag, tell them to read that tag's README instead of trusting this snippet.
- **Which JSON?** The scan action writes `results.json` and, when filtering
  applies, `filtered_results.json` (names configurable via `json_output_file` /
  `filtered_json_output_file`). Convert the **filtered** file when using a baseline
  or severity filter, or the Security tab shows flaws the build deliberately
  ignored.
- **Fork PRs** get a read-only `GITHUB_TOKEN` and cannot write to the Security
  tab. Either use `pull_request_target` deliberately, understanding the risk of
  running untrusted code with elevated permissions, or accept build-break-only
  for forks.
- **`source-base-path-N`** maps scanned module paths back to repo paths. Without
  it, alerts may not anchor to files and look missing.
- **`if: always()`** on both post-scan steps, otherwise a failing gate skips
  publication.

### Pipeline scan action inputs `[v: 2026-09-15]`

`vid`, `vkey`, `file`, `fail_build`, `fail_on_severity`, `fail_on_cwe`,
`baseline_file`, `store_baseline_file`, `store_baseline_file_branch`,
`create_baseline_from` (`standard`|`filtered`), `policy_file`,
`veracode_policy_name`, `timeout`, `issue_details`, `summary_display`,
`json_display`, `verbose`, `summary_output`, `summary_output_file`,
`json_output`, `json_output_file`, `filtered_json_output_file`, `project_name`,
`project_url`, `project_ref`, `app_id`, `development_stage`, `include`.

**Deprecated, removal announced:** `policy_name`, `request_policy` — use
`veracode_policy_name`.

## Policy scan on main

```yaml
jobs:
  policy_scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: mvn -B package --file pom.xml
      - name: Veracode Upload and Scan
        uses: veracode/veracode-uploadandscan-action@v1.1   # tag NOT re-verified
        with:
          appname: 'My-Application'
          createprofile: true
          filepath: 'target/app.jar'
          vid: ${{ secrets.VERACODE_API_KEY_ID }}
          vkey: ${{ secrets.VERACODE_API_KEY_SECRET }}
          # version, sandboxname, createsandbox, failbuild, scantimeout —
          # input names UNVERIFIED; check the action README.
```

Wraps the Java API wrapper (HMAC only). Results land in the application profile
and become queryable through everything in `findings-and-annotations.md` — this
is the bridge between CI and reporting.

## Other Veracode GitHub integrations `[v: 2026-09-15 | docs.veracode.com/r/c_about_github]`

- **Veracode Workflow App** — scans all repos in an org from one config file;
  supports Fix for SCA auto-remediation pull requests.
- **Veracode Fix** — AI-generated patches from pipeline scan results, delivered
  as PRs.

---

# Jenkins, GitLab CI, Azure DevOps

Veracode publishes Pipeline Scan examples for **Azure DevOps, GitHub, GitLab and
Jenkins** `[v: 2026-09-15 | docs.veracode.com/r/r_pipeline_scan_examples]`. The
per-platform snippets download and extract `pipeline-scan-LATEST.zip`, or run the
`veracode/pipeline-scan` Docker image — which Veracode recommends for stability.

**Plugin/extension names, versions and task inputs for these platforms are
unverified in this KB.** Do not invent a Jenkins step name or an Azure DevOps task
identifier. Two honest options:

1. Point at `docs.veracode.com/r/r_pipeline_scan_examples` for that platform's
   snippet.
2. Write the **Docker-based** version, which is portable and does not depend on a
   plugin's input names:

```yaml
# GitLab CI — portable, no plugin required
veracode_pipeline_scan:
  stage: test
  image: veracode/pipeline-scan
  variables:
    VERACODE_API_KEY_ID: $VERACODE_API_KEY_ID
    VERACODE_API_KEY_SECRET: $VERACODE_API_KEY_SECRET
  script:
    - java -jar /opt/veracode/pipeline-scan.jar
        --veracode_api_id "$VERACODE_API_KEY_ID"
        --veracode_api_key "$VERACODE_API_KEY_SECRET"
        --file target/app.jar
        --fail_on_severity "Very High, High"
        --baseline_file baseline.json
        --json_output_file filtered_results.json
  # NOTE: the jar path inside the image is UNVERIFIED — confirm with
  # `docker run --rm -it --entrypoint sh veracode/pipeline-scan`
  artifacts:
    when: always
    paths: [ filtered_results.json ]
```

Offer the portable form when you cannot verify a plugin's interface. It is more
useful than a confident guess, and it works across all four platforms.

Self-hosted runners need Veracode's IP ranges allowlisted — see
`auth-and-access.md`.

## Community projects

`github.com/veracode/Veracode-Community-Projects` collects unofficial
integrations and HMAC signing libraries, including Azure DevOps SAST extensions.
Community-maintained and **not** Veracode-supported — say so when recommending
one.
