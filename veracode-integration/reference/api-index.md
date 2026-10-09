# Veracode API index — full map and re-validation manifest

Two jobs: tell you which API family owns a problem, and give the spec URL to
verify against. Also serves as the **staleness checklist** — re-run the `Verified`
column periodically.

Provenance: `[v: date | source]`. **Untagged or marked *unverified* = do not
assert it. Name the spec and let the user confirm.**

## Base URLs

| Region | REST host | XML base |
|---|---|---|
| US Commercial (default) | `https://api.veracode.com` | `https://analysiscenter.veracode.com/api` |
| European Union | `https://api.veracode.eu` | `https://analysiscenter.veracode.eu/api` |
| US Federal (FedRAMP) | `https://api.veracode.us` | `https://analysiscenter.veracode.us/api` |

`[v: 2026-10-09 | docs.veracode.com/r/Region_Domains_for_Veracode_APIs]`

Always parameterise this. Regional accounts are common and a hardcoded host fails
with a confusing auth error, not a clear one. An HMAC key ID's prefix encodes the
region (`hmac-and-xml-api.md` §2); an OAuth client ID does not, so OAuth users
must say which region they are in.

## REST API families `[v: 2026-09-15 | docs.veracode.com/r/c_rest_intro]`

| API | Base path | Purpose | KB file | Verified |
|---|---|---|---|---|
| Identity | `/api/authn/v2` | Users, teams, roles, business units, API credentials, OAuth clients | `identity.md` | 2026-10-02 (live) |
| Applications | `/appsec/v1/applications` | Application profiles **and the compliance verdict** | `findings-and-annotations.md`, `policy-and-compliance.md` | 2026-09-18 (live) |
| Sandboxes | `/appsec/v1/applications/{guid}/sandboxes` | Development sandboxes | `findings-and-annotations.md` | 2026-09-15 |
| Findings v2 | `/appsec/v2/applications/{guid}/findings` | Consolidated flaw state | `findings-and-annotations.md` | 2026-09-15 |
| Annotations | `/appsec/v2/applications/{guid}/annotations` | Comments and mitigations | `findings-and-annotations.md` | 2026-09-15 |
| Summary Report | `/appsec/v2/applications/{guid}/summary_report` | Compliance + counts summary | `policy-and-compliance.md` | 2026-09-15 |
| Policy | `/appsec/v1/policies` | Policy CRUD and evaluation | `policy-and-compliance.md` | 2026-09-15 (list shape live) |
| Reporting (Analytics) | `/appsec/v1/analytics/report` | Async bulk extraction | `reporting.md` | 2026-09-15 (validation live) |
| Custom PDF | `/report/pdf` | Customizable Report PDF, async | `reporting.md` | partial — docs + spec, not run |
| Pipeline Scan | `/pipeline_scan/v1` | CI scan lifecycle | `pipeline-scan.md` | 2026-09-15 |
| Dynamic Analysis | `/was/configservice/v1` | DAST analyses and scans | `sca-and-dast.md` | partial |
| DAST Essentials | *unverified* | DAST Essentials product | `sca-and-dast.md` | **no** |
| SCA (agent-based) | `/srcclr/v3` | Workspaces, projects, issues, SBOM | `sca-and-dast.md` | partial |
| SCA Annotations | *unverified* | Annotate SCA findings | `sca-and-dast.md` | **no** |
| Healthcheck | *unverified* | API/system status | — | **no** — `veracode-api-py` deprecates its wrapper in favour of `GET /api/authn/v2/users/self` |
| Greenlight | *unverified* | IDE scanning | — | **no** |
| eLearning / Security Labs | *unverified* | Training content | — | **no** |

Families marked **no** exist and are named in Veracode's own index, but this KB
has no verified detail on them. If asked, say exactly that and point at the spec.

## Legacy XML APIs

Still current for things REST cannot do — most importantly **build-scoped
queries** (REST is context-scoped; there is no "findings for scan N" and no
scan-name filter). **HMAC only** — no OAuth. Stricter rate limits (250/min
general, 80/min for `detailedreport.do`).

| Endpoint | Purpose |
|---|---|
| `getapplist.do` / `getsandboxlist.do` / `getbuildlist.do` | Numeric ids; `<build version=…>` is the scan name |
| `getappbuilds.do` | Apps whose results changed since a date — one call |
| `detailedreport.do` | Full results for one build, SAST + SCA |
| `detailedreportpdf.do` / `summaryreportpdf.do` | PDF for one build (works for sandbox builds) |
| `getbuildinfo.do` | Build status |
| `uploadfile.do` / `beginprescan.do` / `beginscan.do` | Upload & Scan lifecycle |

Paths with versions, parameters, parse guards and the attribute sets seen live:
**`hmac-and-xml-api.md`**.

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
docs.veracode.com/r/HMAC_credentials                HMAC lifecycle, one pair per user
docs.veracode.com/r/Region_Domains_for_Veracode_APIs   REST and XML hosts per region
docs.veracode.com/r/c_results_main                  Results XML APIs
docs.veracode.com/r/c_custom_pdf_api                Custom PDF API
```

## Official tooling

| Tool | Auth | Notes |
|---|---|---|
| `veracode-api-py` (PyPI) | HMAC | Python wrapper; broad REST coverage plus XML calls (raw bytes back). 0.9.68's XML calls hardcode the US Commercial host |
| `veracode-api-signing` (PyPI) | HMAC | `RequestsAuthPluginVeracodeHMAC`, `generate_veracode_hmac_header`, the `veracode_hmac_auth` CLI and an httpie plugin. 26.5.0 `[v: 2026-10-09]` |
| Java API wrapper | HMAC | What the Upload & Scan CI plugins wrap |
| Pipeline Scan JAR / Docker | HMAC | `veracode/pipeline-scan` on Docker Hub — preferred over the ZIP |
| `Veracode-Community-Projects` (GitHub) | varies | Community automation, unsupported |

**None of the wrappers accept OAuth.** If a user is on a wrapper, they are on
HMAC, and telling them to switch to Bearer tokens will break their integration.
