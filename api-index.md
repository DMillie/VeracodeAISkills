# Veracode API index — full map and re-validation manifest

Two jobs: tell you which API family owns a problem, and give the spec URL to
verify against. Also serves as the **staleness checklist** — re-run the `Verified`
column periodically.

Provenance: `[v: date | source]`. **Untagged or marked *unverified* = do not
assert it. Name the spec and let the user confirm.**

## Base URLs

| Region | Host |
|---|---|
| US Commercial (default) | `https://api.veracode.com` |
| European Union | `https://api.veracode.eu` |
| US Federal | `https://api.veracode.us` |

Always parameterise this. Regional accounts are common and a hardcoded host fails
with a confusing auth error, not a clear one.

## REST API families `[v: 2026-09-15 | docs.veracode.com/r/c_rest_intro]`

| API | Base path | Purpose | KB file | Verified |
|---|---|---|---|---|
| Identity | `/api/authn/v2` | Users, teams, roles, business units, API credentials | `identity.md` | 2026-09-15 |
| Applications | `/appsec/v1/applications` | Application profiles | `findings-and-annotations.md` | 2026-09-15 |
| Sandboxes | `/appsec/v1/applications/{guid}/sandboxes` | Development sandboxes | `findings-and-annotations.md` | 2026-09-15 |
| Findings v2 | `/appsec/v2/applications/{guid}/findings` | Consolidated flaw state | `findings-and-annotations.md` | 2026-09-15 |
| Annotations | `/appsec/v2/applications/{guid}/annotations` | Comments and mitigations | `findings-and-annotations.md` | 2026-09-15 |
| Summary Report | `/appsec/v2/applications/{guid}/summary_report` | Compliance + counts summary | `policy-and-compliance.md` | 2026-09-15 |
| Policy | `/appsec/v1/policies` | Policy CRUD and evaluation | `policy-and-compliance.md` | 2026-09-15 |
| Reporting (Analytics) | `/appsec/v1/analytics/report` | Async bulk extraction | `reporting.md` | 2026-09-15 |
| Pipeline Scan | `/pipeline_scan/v1` | CI scan lifecycle | `pipeline-scan.md` | 2026-09-15 |
| Dynamic Analysis | `/was/configservice/v1` | DAST analyses and scans | `sca-and-dast.md` | partial |
| DAST Essentials | *unverified* | DAST Essentials product | `sca-and-dast.md` | **no** |
| SCA (agent-based) | `/srcclr/v3` | Workspaces, projects, issues, SBOM | `sca-and-dast.md` | partial |
| SCA Annotations | *unverified* | Annotate SCA findings | `sca-and-dast.md` | **no** |
| Healthcheck | *unverified* | API/system status | — | **no** |
| Custom PDF | *unverified* | Custom PDF reports | — | **no** |
| Greenlight | *unverified* | IDE scanning | — | **no** |
| eLearning / Security Labs | *unverified* | Training content | — | **no** |

Families marked **no** exist and are named in Veracode's own index, but this KB
has no verified detail on them. If asked, say exactly that and point at the spec.

## Legacy XML APIs

Still current for things REST cannot do — most importantly **build-scoped
queries** (REST is context-scoped; there is no "findings for scan N").

| Endpoint | Purpose |
|---|---|
| `detailedreport.do` | Full results for one build |
| `buildinfo.do` | Build status and ID |
| `getbuildlist.do` | Builds for an application |
| `upload.do` / `beginscan.do` | Upload & Scan lifecycle |
| `getpolicylist.do` | Policy list |

Host `analysiscenter.veracode.com`. **HMAC only** — no OAuth. Stricter rate
limits (see `auth-and-access.md`). Detail *unverified* in this KB; treat XML
parameter names as things to look up, not recall.

## Spec URLs for verification

SwaggerHub, under the `Veracode` organization:

```
https://app.swaggerhub.com/apis/Veracode/veracode-findings_api_specification/2.0
https://app.swaggerhub.com/apis/Veracode/veracode-applications_api_specification/1.0
https://app.swaggerhub.com/apis/Veracode/veracode-policy_api_specification/1.0
https://app.swaggerhub.com/apis/Veracode/veracode-static_finding_data_path_api/v2
https://app.swaggerhub.com/apis/Veracode/veracode-greenlight_api_specification/v3
```

Annotations, Identity, Reporting, Dynamic Analysis, Pipeline Scan and SCA specs
follow the same `veracode-<name>_api_specification` naming but their exact slugs
and versions are **unverified** — browse the Veracode org listing rather than
guessing a URL.

**Note:** SwaggerHub renders client-side. A plain HTTP fetch of an `app.swaggerhub.com`
URL returns an empty shell. Use the "Download API" / raw spec option, or the
`docs.veracode.com` page for that API.

## Doc pages worth citing to users

```
docs.veracode.com/r/c_rest_intro                    REST API index
docs.veracode.com/r/OAuth_Client_credentials        OAuth setup
docs.veracode.com/r/c_api_credentials3              Credential types
docs.veracode.com/r/c_API_roles                     Which role grants which API
docs.veracode.com/r/About_API_Rate_Limiting         Rate limits
docs.veracode.com/r/c_findings_v2_examples          Findings query examples
docs.veracode.com/r/c_rest_annotations_intro        Annotations
docs.veracode.com/r/Reporting_REST_API              Reporting API
docs.veracode.com/r/c_policy_rest_api               Policy API
docs.veracode.com/r/c_identity_intro                Identity API
docs.veracode.com/r/c_dynamic_intro                 Dynamic Analysis
docs.veracode.com/r/c_sourceclear_intro             SCA
docs.veracode.com/r/c_about_github                  GitHub integrations
docs.veracode.com/r/r_pipeline_scan_examples        Pipeline Scan CI examples
```

## Official tooling

| Tool | Auth | Notes |
|---|---|---|
| `veracode-api-py` (PyPI) | HMAC | Python wrapper; broad coverage; friendlier enum aliases than raw REST |
| `veracode-api-signing` (PyPI) | HMAC | `RequestsAuthPluginVeracodeHMAC` for your own scripts |
| Java API wrapper | HMAC | What the Upload & Scan CI plugins wrap |
| Pipeline Scan JAR / Docker | HMAC | `veracode/pipeline-scan` on Docker Hub — preferred over the ZIP |
| `Veracode-Community-Projects` (GitHub) | varies | Community automation, unsupported |

**None of the wrappers accept OAuth.** If a user is on a wrapper, they are on
HMAC, and telling them to switch to Bearer tokens will break their integration.
