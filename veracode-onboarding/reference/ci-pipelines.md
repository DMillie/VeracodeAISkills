# CI pipelines — PR gates and policy scans

For customers not using repository scanning (Bitbucket, GitHub Enterprise Server,
US Federal, Jenkins and other CI), or who want per-pipeline control. Action tags
`[v: 2026-10-09 | git ls-remote]`; inputs read from each action's `action.yml`.

---

## 1. Two jobs, not one

| Trigger | Scan | Gives | Reaches the Platform? |
|---|---|---|---|
| Pull request | **Pipeline Scan** | Minutes; pass/fail on the PR; JSON results in the run | **No** |
| Push to main / release | **Upload & Scan (policy scan)** | The compliance verdict; history; reports | **Yes** |

A PR gate on Upload & Scan is too slow and clutters the application profile. A
compliance report built on Pipeline Scan finds nothing, because Pipeline Scan
results never leave the CI run. Customers usually want both — two jobs.

Both need the **HMAC** API ID and key of an **API service account**
(`platform-setup.md` §3–4), stored as CI secrets. Never OAuth here.

**Build first.** Every job packages the app before scanning: the language's
build plus Veracode's packaging rules, or `veracode package` (`cli-and-packaging.md`).

## 2. GitHub Actions

### PR gate — Pipeline Scan, with Security tab publishing

```yaml
name: Veracode PR scan
on:
  pull_request:
    branches: [ main ]
permissions:
  contents: read
  security-events: write              # only needed for the Security tab
jobs:
  pipeline_scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: mvn -B package --file pom.xml          # or: veracode package ...
      - name: Veracode Pipeline Scan
        uses: veracode/Veracode-pipeline-scan-action@v1.0.25
        with:
          vid: ${{ secrets.VERACODE_API_KEY_ID }}     # HMAC
          vkey: ${{ secrets.VERACODE_API_KEY_SECRET }}
          file: target/app.jar
          fail_build: true
          fail_on_severity: 'Very High, High'        # English strings here
          baseline_file: baseline.json               # see §4 — without it, day one fails
      - name: Convert to SARIF
        if: always()
        uses: veracode/veracode-pipeline-scan-results-to-sarif@v2.0.5
        with:
          scan-type: pipeline
          results-json: filtered_results.json
          output-results-sarif: veracode-results.sarif
          githubToken: ${{ secrets.GITHUB_TOKEN }}
          ref: ${{ github.ref }}
          commitSHA: ${{ github.sha }}
      - name: Publish to the Security tab
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: veracode-results.sarif
```

Converting to SARIF publishes nothing; the upload step does. Fork PRs cannot write
to the Security tab with the default token.

### Policy scan on main — Upload & Scan

```yaml
on:
  push:
    branches: [ main ]
jobs:
  policy_scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: mvn -B package --file pom.xml
      - name: Veracode Upload and Scan
        uses: veracode/veracode-uploadandscan-action@0.2.11   # tags are 0.x; there is no v1
        with:
          appname: 'Payments Service'        # match the agreed profile name
          createprofile: true
          filepath: target/app.jar
          version: 'main ${{ github.sha }}'  # the SCAN NAME — see §5
          vid: ${{ secrets.VERACODE_API_KEY_ID }}
          vkey: ${{ secrets.VERACODE_API_KEY_SECRET }}
          scantimeout: 60                    # wait for results, so the job can fail on policy
          deleteincompletescan: 1            # don't block on a stuck earlier scan
```

There is **no `failbuild` input**. Without `scantimeout` the action uploads and
returns immediately — fine for a nightly job, not for a gate. Other inputs worth
knowing: `sandboxname` + `createsandbox` (send to a sandbox instead), `criticality`
and `teams` (used when `createprofile` creates the profile), `policy`, `include`
/ `exclude` (module selection).

## 3. Other CI systems

Veracode publishes Pipeline Scan examples for **Azure DevOps, GitLab and Jenkins**
at `docs.veracode.com/r/r_pipeline_scan_examples`, and recommends the
**`veracode/pipeline-scan` Docker image** over downloading the ZIP. There are also
an Azure DevOps extension and a Jenkins plugin; check their current task and step
names in Veracode's docs rather than recalling them.

The portable pattern works anywhere a container runs:

```yaml
# GitLab CI example — the same commands work in any CI that can run a container
veracode_pipeline_scan:
  stage: test
  image: veracode/pipeline-scan
  script:
    - java -jar /opt/veracode/pipeline-scan.jar     # confirm the jar path in the image
        --veracode_api_id "$VERACODE_API_KEY_ID"
        --veracode_api_key "$VERACODE_API_KEY_SECRET"
        --file target/app.jar
        --fail_on_severity "Very High, High"
        --baseline_file baseline.json
  artifacts:
    when: always
    paths: [ results.json, filtered_results.json ]
```

Or install the Veracode CLI in the job and run `veracode package` then
`veracode static scan` — note the CLI's flags use hyphens (`--fail-on-severity`)
where the JAR's use underscores.

Self-hosted runners need Veracode's IP ranges allowlisted. A timeout during
upload that looks like a Veracode outage is usually the firewall.

## 4. Baselines — why PR gates survive

Without a baseline, the first PR gate fails on every flaw that already exists, and
the team turns the gate off within a week.

1. Scan `main` once and keep the results as `baseline.json` (commit it, or use the
   action's `store_baseline_file` options).
2. Pass `baseline_file` on PRs so only **new** flaws fail.
3. Refresh the baseline when `main` moves.

`veracode/veracode-pipeline-mitigation` builds a baseline from the **approved**
mitigations on an application's policy or sandbox scan, so the PR gate stops
re-reporting flaws AppSec has already accepted. Proposed-but-unapproved
mitigations are not included.

## 5. Name scans for the questions that come later

`version` (Upload & Scan) becomes the scan's name in the Platform. The default
(`Scan from Github job: …`) answers nothing. Months later someone will ask for
"the findings from the last release", and the only way to find that scan
programmatically is by its name. Agree a convention now, for example:

- release builds: `Release ${{ github.ref_name }}`
- main: `main ${{ github.sha }}`

If release and branch builds share a sandbox, the sandbox's current results flip
with whichever scanned last. Keep release scans in the policy scan or a dedicated
sandbox.

## 6. Turning the gate on without a revolt

1. Week 1: Pipeline Scan on PRs with `fail_build: false` — results visible,
   nothing blocked. Policy scan on main nightly.
2. Week 2: baseline in place; `fail_build: true` on **Very High** only.
3. Later: add High, or move to `veracode_policy_name` so the PR gate matches the
   policy the verdict uses.

Announce each step to developers before it happens, with where results appear and
whom to ask.

---

## Where it goes wrong

| Symptom | Usual cause |
|---|---|
| `401` in CI | OAuth credentials in `vid`/`vkey` (must be HMAC), wrong region, or expired keys |
| PR gate fails on everything at once | No baseline |
| Security tab empty after "successful" SARIF conversion | Missing upload step or `security-events: write` |
| Security tab shows flaws the build ignored | Converted `results.json` instead of `filtered_results.json` |
| Platform shows no new scan after merge | Only Pipeline Scan configured; add Upload & Scan |
| Upload & Scan job "passes" but the app fails policy | No `scantimeout`, so the job never waited for the verdict |
| `uses: …uploadandscan-action@v1…` fails to resolve | That tag does not exist; pin `0.2.11` (or newer 0.x) |
| Upload & Scan fails: a scan is already in progress | A stuck earlier scan; `deleteincompletescan: 1` or clear it in the Platform |
| Profiles multiply | `appname` differs from the agreed profile name (default is `owner/repo`) |
