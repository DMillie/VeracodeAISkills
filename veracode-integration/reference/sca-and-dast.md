# SCA and DAST

**Coverage warning:** this is the thinnest file in the KB. Several endpoint sets
here are **unverified**. Say so, give the shape and the spec URL, and let the
user confirm — do not fill the gaps from memory.

---

# SCA (Software Composition Analysis)

## Two different products with the same name

The single biggest source of confusion. Establish which one the user means before
writing anything.

| | **Upload-based SCA** | **Agent-based SCA** |
|---|---|---|
| How it runs | Part of an Upload & Scan of the artifact | `srcclr` agent against source / build |
| Organized by | Application profile | **Workspace → Project** |
| Read results via | Findings API, `scan_type=SCA` | SCA REST API (`/srcclr/v3`) |
| Auth | Standard API service account | **UI user account, not a service account** |
| Fits the app-profile hierarchy | Yes | **No** |

If a user asks to "get SCA findings for application X" and their results live in
agent-based scans, the Findings API will return nothing and look broken.

## Upload-based SCA via the Findings API [INT-82~]

`GET /appsec/v2/applications/{guid}/findings?scan_type=SCA`

- `scan_type=SCA` **cannot be combined** with STATIC/DYNAMIC/MANUAL. Separate call.
- Extra params: `cve`, `cvss`, `cvss_gte`, `sca_scan_mode`, `sca_dep_mode`
  (last two: enum values **unverified**).
- `finding_details` for SCA: `severity`, `cve.{name,cvss,severity,href}`, `cwe`,
  `component_filename`, `component_id`, `component_path[]`, `product_id`,
  `version`, `language`, `licenses[]`, `metadata`.
- **`severity` is a string in the spec but was an integer 2–5 on a live tenant**
  (all 1,082 SCA findings); the string, if you want it, is at `cve.severity`
  [INT-87]. Handle both shapes. Dynamic findings: fields not captured (below).

```python
# SCA branch — do NOT reuse the STATIC field paths
SEVWORD = {"VERY HIGH": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "VERY LOW": 1, "INFORMATIONAL": 0}
for f in sca_findings:
    d = f["finding_details"]
    sev = d["severity"]                       # int on the tenant seen, str per the spec
    sev = sev if isinstance(sev, int) else SEVWORD.get(str(sev).upper().replace("_", " "))
    print(d["cve"]["name"], d["component_filename"], sev)
```

### No fix version in the Findings API

A live SCA finding carried no fix, safe-version or upgrade field of any kind
[INT-88]. Fields seen: `component_filename`, `component_id`, `component_path[].path`,
`version`, `product_id`, `language`, `licenses[]`, `metadata.sca_dep_mode`,
`metadata.sca_scan_mode`, `severity`, `cve.{name,cvss,cvss3,severity,vector,href}`,
`cve.exploitability.{epss_*,exploit_observed,…}`, `cwe.{id,name,href}`. So this
API cannot tell you which version to upgrade to. Where to get one (the SCA
agent's scan output is the candidate) is **not verified**; say so rather than
computing a "safe version" from the finding.

## Upload-based SCA for one specific build (XML)

The Findings API gives the current consolidated SCA state. For **one build**
(for example the newest release scan), read the `software_composition_analysis`
section of `detailedreport.do` — HMAC only. Two levels: `<component>` is the
inventory and its `<vulnerability>` children are the CVEs. Full attribute sets
and parse guards: `hmac-and-xml-api.md` §7–8.

Facts that change how SCA is reported [INT-83]:

- **A build's SCA results grow after the scan.** Veracode re-matches newly
  published CVEs against existing inventory without a rescan; 7 of 237 CVEs in
  one tenant appeared up to 8 days after their build was scanned. Separate
  "known at release" from "discovered since".
- `first_found_date` is when Veracode first saw the CVE **in this application**,
  not when the CVE was published. No publication date exists in the upload-based
  results; for CVE age use the agent-based API or NVD.
- There is **no open/closed status** on an upload-based SCA vulnerability, only a
  `mitigation` true/false flag.

## Agent-based SCA REST API [INT-84~]

Base path `/srcclr/v3`. Spec: Veracode SCA Agent API Specification v3.0 on
SwaggerHub.

Documented capabilities: retrieve, delete, insert and update agent-scan data;
query vulnerabilities; annotate findings; **generate SBOMs**.

Two non-obvious requirements:

- **`accept-encoding: gzip` and a `user-agent` header are required.** Requests
  without them may be rejected. `requests` sets both by default; hand-rolled
  clients and `curl` scripts often do not.
- **Requires a UI user account, not an API service account.** Seen live:
  `/srcclr/v3/*` returned `403` for an API service account [INT-89]. The cause
  was not verified (the role or workspace grant it lacks is unknown), so report
  "not accessible" instead of retrying.

Exact endpoint paths for workspaces, projects, issues, agents, teams and
components are **unverified** — the resource names above come from the product's
own vocabulary, not from a spec this KB has read. Confirm before use.

## SCA annotations

A separate SCA Annotations API exists
(`docs.veracode.com/r/c_rest_sca_annotations`). Path and schema **unverified**.

**Do not assume `/appsec/v2/applications/{guid}/annotations` accepts SCA
`issue_id`s.** If a user wants to mitigate SCA findings, flag this as the thing
to verify first. A mitigation-review tool built on the Findings API covered
STATIC only for this reason; SCA mitigations were not tried.

## SBOM

SBOM generation is a documented SCA capability. Endpoint and output format
(CycloneDX/SPDX, versions) **unverified**. Do not name a format you have not
confirmed.

---

# DAST

## Two products again

| | **Dynamic Analysis** | **DAST Essentials** |
|---|---|---|
| Base path | `/was/configservice/v1` | **unverified** |
| Model | Analyses containing URL scans, linked to app profiles | Separate product surface |
| Results | Findings API, `scan_type=DYNAMIC` | unverified |

## Dynamic Analysis REST API [INT-85~]

Base path: `https://api.veracode.com/was/configservice/v1`

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/analyses` | Create an analysis with URL scans |
| `PUT` | `/analyses` | Configure analyses and URL scans |
| `GET` | `/code_groups/errorcode` | Look up authentication error codes |

Query parameter on POST/PUT: `scan_type=API_SCAN` for API scanning;
`scan_type=WEB_SCAN` (default) for web application scanning.

Documented capabilities: create analyses with URL scans, configure them, schedule
and run them, and link them to Veracode application profiles.

**Endpoints for scans, schedules, occurrences, scanner variables and results are
not captured here.** They exist in the Dynamic Analysis spec on SwaggerHub. If a
user needs them, say the KB stops here and name the spec.

## DAST Essentials REST API

`docs.veracode.com/r/DAST_Essentials_REST_API` — **nothing verified.** Base path,
auth model and endpoints are all unknown to this KB. Treat any DAST Essentials
question as out of scope and point at that page.

## Reading DAST findings

Dynamic Analysis results reach the application profile, so
`GET /appsec/v2/applications/{guid}/findings?scan_type=DYNAMIC` returns them.
The **`finding_details` schema for DYNAMIC findings is unverified** — it is not
the STATIC schema. Fetch one finding and inspect before writing field access, or
use `dynamic_flaw_info` for request/response detail.

---

## What to say when asked something this file does not cover

> The KB I'm working from covers Dynamic Analysis at the `/was/configservice/v1`
> base path and the analyses endpoints, but not the scans/schedules/results
> endpoints you need. Rather than guess parameter names, check the Dynamic
> Analysis spec on SwaggerHub under the Veracode org — I can write the surrounding
> script and leave the call signature for you to fill from the spec.

That is a better answer than a confident invented endpoint, and it is the
behaviour this KB is designed to produce.
