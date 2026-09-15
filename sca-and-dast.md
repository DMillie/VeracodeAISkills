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

## Upload-based SCA via the Findings API `[v: 2026-09-15 | Findings OpenAPI model]`

`GET /appsec/v2/applications/{guid}/findings?scan_type=SCA`

- `scan_type=SCA` **cannot be combined** with STATIC/DYNAMIC/MANUAL. Separate call.
- Extra params: `cve`, `cvss`, `cvss_gte`, `sca_scan_mode`, `sca_dep_mode`
  (last two: enum values **unverified**).
- `finding_details` for SCA: `severity` (**string**, unlike STATIC's int),
  `cve.{name,cvss,severity,href}`, `cwe`, `component_filename`, `component_id`,
  `component_path[]`, `product_id`, `version`, `language`, `licenses[]`, `metadata`.

```python
# SCA branch — do NOT reuse the STATIC field paths
for f in sca_findings:
    d = f["finding_details"]
    print(d["cve"]["name"], d["component_filename"], d["severity"])  # severity is a str
```

## Agent-based SCA REST API `[v: 2026-09-15 | docs.veracode.com/r/c_sourceclear_intro]`

Base path `/srcclr/v3`. Spec: Veracode SCA Agent API Specification v3.0 on
SwaggerHub.

Documented capabilities: retrieve, delete, insert and update agent-scan data;
query vulnerabilities; annotate findings; **generate SBOMs**.

Two non-obvious requirements:

- **`accept-encoding: gzip` and a `user-agent` header are required.** Requests
  without them may be rejected. `requests` sets both by default; hand-rolled
  clients and `curl` scripts often do not.
- **Requires a UI user account, not an API service account.**

Exact endpoint paths for workspaces, projects, issues, agents, teams and
components are **unverified** — the resource names above come from the product's
own vocabulary, not from a spec this KB has read. Confirm before use.

## SCA annotations

A separate SCA Annotations API exists
(`docs.veracode.com/r/c_rest_sca_annotations`). Path and schema **unverified**.

**Do not assume `/appsec/v2/applications/{guid}/annotations` accepts SCA
`issue_id`s.** If a user wants to mitigate SCA findings, flag this as the thing
to verify first.

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

## Dynamic Analysis REST API `[v: 2026-09-15 | docs.veracode.com/r/c_dynamic_intro]`

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
