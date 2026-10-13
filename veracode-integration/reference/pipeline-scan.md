# Pipeline Scan — REST API, CLI and Docker

**Traps in this file:** Pipeline Scan results **never reach the Findings API** ·
its policy evaluation is local · without a baseline the gate fails on the entire
existing backlog on day one · `binary_hash` must be a real SHA-256 of the file.

Use Pipeline Scan for fast PR feedback. Use Policy (Upload & Scan) for anything
that has to appear in the Veracode Platform, drive compliance, or be queried by
the Findings API later.

---

## When to use the REST API directly

Most users should use the prebuilt integration for their CI system
(`ci-integrations.md`) or the Docker image. Go to the raw REST API when:

- the CI system has no Veracode plugin
- they need to orchestrate scans from their own service
- a plugin is failing and you need to reproduce the underlying calls

## REST lifecycle `[v: 2026-09-15 | docs.veracode.com/r/Configuring_a_Pipeline_Scan_with_the_REST_API]`

Base path: `https://api.veracode.com/pipeline_scan/v1`

```
1. POST   /scans                                  create — returns scan_id
2. POST   /scans/{scan_id}/segments/{segment_no}   upload the binary in segments
3. PUT    /scans/{scan_id}                         start
4. GET    /scans/{scan_id}                         poll status
5. GET    /scans/{scan_id}/findings                results
6. DELETE /scans/{scan_id}                         cancel
```

### 1. Create

```jsonc
{
  "binary_name": "verademo.war",
  "binary_size": 6577398,
  "binary_hash": "48c96bf1ff8b47316683c99376b67b455f0e4a2d9705323fa3bcbe71afe350c7",
  "project_name": "verademo",
  "project_uri": "https://github.com/veracode/verademo",
  "dev_stage": "DEVELOPMENT"
}
```

`binary_name`, `binary_size` and `binary_hash` are **required**. The hash is a
SHA-256 of the file; compute it, never fake it:

```python
import hashlib, os
p = "target/app.jar"
h = hashlib.sha256(open(p, "rb").read()).hexdigest()
size = os.path.getsize(p)
```

`dev_stage` values seen: `DEVELOPMENT`. Full enum (`TESTING`, `RELEASE`?)
**unverified**.

### 2–4. Segments, start, poll

The response to create includes a `UPLOADING` status. Segment count and maximum
segment size are **unverified** — check the Pipeline Scan spec before choosing a
chunk size. Other status values beyond `UPLOADING` are **unverified**; inspect
the polling response and pin the terminal condition rather than assuming
`SUCCESS`/`FAILED`.

Timeouts are configurable — see
`docs.veracode.com/r/Using_Pipeline_Scan_Timeouts_with_the_REST_API`.

### 5. Findings

`GET /scans/{scan_id}/findings`. Schema is Pipeline-Scan-specific and **not the
`/appsec/v2` Finding schema** — do not reuse `finding_details.cwe.id` paths
without checking.

---

## CLI and Docker `[v: 2026-09-15 | docs.veracode.com/r/r_pipeline_scan_examples]`

Veracode recommends the **Docker image over the ZIP download** for stability:

```
docker pull veracode/pipeline-scan
```

The ZIP is `pipeline-scan-LATEST.zip`; most CI examples download and extract it,
then run `java -jar pipeline-scan.jar`.

The **Veracode CLI** also runs a Pipeline Scan: `veracode static scan <artifact>`
with `--fail-on-severity`, `--fail-on-cwe`, `--baseline-file`, `--results-file`,
`--policy-file` and `--summary-output`; exit code 3 when flaws match the criteria.
Its results stay local like any Pipeline Scan, and `veracode package` builds the
artifact for it `[v: 2026-10-09 | docs.veracode.com/r/veracode_static_scan]`.
Note the CLI's flags use hyphens where the JAR's use underscores.

### Flags

| Flag | Purpose |
|---|---|
| `-f`, `--file` | Artifact to scan |
| `--fail_on_severity` | Fail on these severities, e.g. `"Very High, High"` |
| `--fail_on_cwe` | Fail on specific CWEs, e.g. `80` |
| `--policy_file` | Rate findings against a downloaded policy file |
| `--policy_name` | Rate findings against a named Veracode policy |
| `-bf`, `--baseline_file` | Compare against a baseline; report only new flaws |
| `-jo`, `--json_output` | Emit JSON results |
| `--json_output_file` | JSON results filename |
| `--timeout` | Scan timeout |
| `--issue_details` | Include detail in output |

`--fail_on_severity` takes **English severity strings**, unlike the REST API's
integers. This is a genuine inconsistency in the product, not an error to correct.

---

## Baselines — the reason PR gates survive

Without a baseline, the first run fails on every pre-existing flaw and the team
disables the gate within a week. Design for this from the start.

Pattern:

1. On `main`, run a scan and store the results as the baseline (commit it, or use
   the plugin's baseline-storage options).
2. On `pull_request`, pass `--baseline_file` so only newly introduced flaws fail.
3. Refresh the baseline when `main` moves.

**`veracode/veracode-pipeline-mitigation`** pulls **approved** mitigations from an
application's policy or sandbox scan and emits a Pipeline Scan baseline file
`[v: 2026-09-15 | github.com/veracode/veracode-pipeline-mitigation]`. This is how
you stop the PR gate re-reporting flaws that AppSec has already formally accepted
— otherwise developers see "failures" for risks the security team signed off on,
which destroys trust in the gate faster than anything else.

Proposed-but-not-approved mitigations are **not** included.

---

## Packaging — the silent failure

Veracode scans **built artifacts**, not source. Packaging requirements differ
sharply by language: debug symbols for .NET, what to include for Node and Python,
excluding test code everywhere.

A wrongly packaged submission **scans successfully and reports almost nothing**,
which reads as "we're clean." This is the most dangerous failure mode in the whole
product because it produces a green build and a false sense of safety.

If a user has not shown you a build step, ask what they are submitting before
writing the pipeline. Veracode publishes per-language packaging requirements and
a `veracode package` CLI command; the specifics are **not captured in this KB** —
point them there rather than guessing their build.

---

## Pipeline vs Policy, one more time

| | Pipeline Scan | Policy / Upload & Scan |
|---|---|---|
| Speed | Minutes | Longer |
| Trigger | `pull_request` | `push` to main / release |
| Results location | CI run, local JSON | Application profile |
| Queryable by Findings API | **No** | Yes |
| Affects compliance | **No** | Yes |
| Policy evaluation | Local, advisory | Authoritative |

Teams frequently want both: a Pipeline gate on PRs and a nightly or per-release
Policy scan on main. That is two jobs, not one — say so rather than trying to
serve both from a single workflow.
