# CI/CD integrations

**Traps in this file:** converting results to SARIF does **not** publish them —
a separate upload step does · plugin credentials are **HMAC**, never OAuth ·
`fail_on_severity` takes English strings while the REST API takes integers ·
fork PRs cannot write to the GitHub Security tab.

Version tags are `[v: 2026-10-09 | git ls-remote]` unless marked. Tags rot —
verify before pinning, or tell the user you are quoting a snapshot.

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
        uses: veracode/Veracode-pipeline-scan-action@v1.0.25   # [v: 2026-10-09]
        with:
          vid: ${{ secrets.VERACODE_API_KEY_ID }}      # HMAC id, NOT an OAuth client id
          vkey: ${{ secrets.VERACODE_API_KEY_SECRET }}
          file: 'target/app.jar'
          fail_build: true
          fail_on_severity: 'Very High, High'          # English strings here
          baseline_file: 'baseline.json'               # see pipeline-scan.md

      - name: Convert results to SARIF
        if: always()                                   # previous step failed on purpose
        uses: veracode/veracode-pipeline-scan-results-to-sarif@v2.0.5   # [v: 2026-10-09]
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
        uses: veracode/veracode-uploadandscan-action@0.2.11   # [v: 2026-10-09] tags are 0.x — there is no v1
        with:
          appname: 'My-Application'          # default: ${{ github.repository }}
          createprofile: true
          filepath: 'target/app.jar'
          version: 'Release ${{ github.ref_name }} (${{ github.run_number }})'   # = the SCAN NAME
          vid: ${{ secrets.VERACODE_API_KEY_ID }}
          vkey: ${{ secrets.VERACODE_API_KEY_SECRET }}
          scantimeout: 60                    # minutes to wait for results; what makes it able to break the build
          deleteincompletescan: 1            # clear a stuck previous scan instead of failing
          # sandboxname / createsandbox: send it to a sandbox instead of the policy scan
```

Inputs read from the action's `action.yml` at `0.2.11` `[v: 2026-10-09]`:
`appname`, `createprofile`, `filepath`, `version`, `vid`, `vkey` (required, some
with defaults); `createsandbox`, `sandboxname`, `sandboxid`, `scantimeout`,
`scanpollinginterval`, `deleteincompletescan`, `include`, `exclude`,
`criticality`, `teams`, `policy`, `pattern`, `replacement`, `toplevel`,
`selected`, `selectedpreviously`, `scanallnonfataltoplevelmodules`,
`includenewmodules`, `maxretrycount`, `javawrapperversion`, `debug`. There is
**no `failbuild` input** — without `scantimeout` the action uploads and returns
without waiting.

**Set `version` deliberately.** It becomes the scan name. Later questions like
"the findings from the latest *release* scan" can only be answered by matching on
scan names (`hmac-and-xml-api.md` §6), and the default
(`Scan from Github job: …`) carries no release information.

Wraps the Java API wrapper (HMAC only). Results land in the application profile
and become queryable through everything in `findings-and-annotations.md` — this
is the bridge between CI and reporting.

## Other Veracode GitHub integrations `[v: 2026-09-15 | docs.veracode.com/r/c_about_github]`

- **Veracode Workflow App / GitHub Workflow Integration ("repository
  scanning")** — scans every repo in an org from one private `veracode` repo
  (template: `github.com/veracode/github-actions-integration`) with a central
  `veracode.yml` and `repo_list.yml`; Pipeline Scan SAST, agent-based SCA,
  IaC/secrets; Fix for SCA pull requests. Results reach the Platform only with
  `analysis_on_platform: true` (default `false`). Also exists for Azure DevOps and
  GitLab; not for Bitbucket, GitHub Enterprise Server or the US Federal region
  `[v: 2026-10-09 | docs.veracode.com/r/SCM_integrations]`. Setup is an
  onboarding task — the veracode-onboarding skill walks through it.
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
