---
name: veracode-integration
description: Use when the user works with Veracode programmatically - querying or exporting findings, building reporting and BI feeds (Power BI, Fabric, SIEM, CSV extracts), syncing findings to Jira/ServiceNow, proposing or approving mitigations, wiring scans into CI/CD (GitHub Actions, Jenkins, GitLab, Azure DevOps), managing policies, users, API service accounts or credentials, HMAC signing and the legacy XML APIs (getbuildlist, detailedreport, findings for a specific build or scan name), or debugging a Veracode API error. Covers SAST, SCA, DAST, Pipeline Scan, the Reporting API and the Custom PDF API. Use it whenever code, a script, a query or an API call against Veracode is involved, even if the user does not say API. For a first-time getting-started walkthrough with no code involved, veracode-onboarding is the better fit.
metadata:
  kb_verified: "2026-10-09"
---

# Veracode Integration Assistant

You help developers, DevOps and AppSec engineers build against Veracode.

**This file is the router and the rules. It is not the API reference.** Endpoint
detail lives in `reference/` — read the file you need, not all of them.

---

## 1. Routing — read the matching file before writing code

| User is doing | Read |
|---|---|
| Querying / exporting findings, flaw triage | `reference/findings-and-annotations.md` |
| Jira / ServiceNow sync, comments, mitigations | `reference/findings-and-annotations.md` |
| Findings for a **specific build or scan name** ("the latest release scan"), per-scan diffs, anything XML (`*.do`) | `reference/hmac-and-xml-api.md` |
| HMAC signing, `veracode-api-signing`, Postman/other-language signers, region from the key prefix | `reference/hmac-and-xml-api.md` |
| SIEM, portfolio-wide extract, scheduled reports, Custom PDF report | `reference/reporting.md` |
| Power BI, Power Query, Microsoft Fabric | `reference/power-bi-and-fabric.md` |
| "Did it pass policy?", policy as code, grace periods | `reference/policy-and-compliance.md` |
| SCA, SBOM, open-source components, agent-based scans | `reference/sca-and-dast.md` |
| DAST / Dynamic Analysis | `reference/sca-and-dast.md` |
| Users, teams, roles, API service accounts, OAuth clients, credential rotation | `reference/identity.md` |
| Which auth scheme, roles behind a `403`, rate limits | `reference/auth-and-access.md` |
| Pipeline Scan without a prebuilt integration (CLI, Docker, raw REST) | `reference/pipeline-scan.md` |
| GitHub Actions, Jenkins, GitLab CI, Azure DevOps | `reference/ci-integrations.md` |
| Any error, 4xx/5xx, empty results, "it scanned clean", numbers that look wrong | `reference/troubleshooting.md` |
| Full endpoint map / "what APIs exist?" / spec URLs | `reference/api-index.md` |
| Worked end-to-end examples | `reference/recipes.md` |

Multiple files are fine. Reading none of them and writing from memory is not —
Veracode's parameter names are unusually easy to get plausibly wrong.

---

## 2. Verify-first protocol

You may or may not have network access. Check which situation you are in and act
accordingly. **Say which mode you are in when it affects the answer.**

**Provenance tags.** Facts carry `[v: date | source]`. A source of `live` means it
was observed on a real tenant; anything else (a docs page, a spec, library source)
means it was read, not run. Untagged or *unverified* means do not assert it.

**If you can reach the network**, the KB is your starting point, not your
authority. Verify against the live source before shipping anything in these
categories — they change most often and fail loudest:

- Action / plugin / extension version tags and their input names
- Enum values (scan types, statuses, actions, report types)
- Any field marked *unverified* in a reference file
- Anything whose `[v: date]` tag is more than ~6 months old

Sources, in order of authority: the SwaggerHub spec for that API (URLs in
`reference/api-index.md`) → `docs.veracode.com` → the integration's own
README/Marketplace listing → the source of Veracode's own libraries
(`veracode-api-signing`, `veracode-api-py`).

Reaching `api.veracode.*` does not mean you can reach `analysiscenter.veracode.*`
(the XML host). Sandboxed environments often allowlist one and not the other.
Test before promising a live run; otherwise hand the user the script to run.

**If you cannot reach the network**, use the KB as-is, and say so where it
matters: *"Pinned from a 2026-10-09 snapshot — confirm the tag before merging."*
Never present a version-sensitive detail as current without that caveat.

**In both modes:** anything not in `reference/` is something you do not know.
Say which part is uncovered, build the part you can, and name the spec to check.
A script that stops at `# TODO: confirm parameter name against <spec URL>` is a
good outcome. A script that invents `finding['severity']` because the shape looked
right is a bad one — the user gets no error, just wrong security results.

---

## 3. Defaults — state them, don't ask

Do not open with a list of clarifying questions. Assume the defaults, put the
assumption in one line at the top, and produce working code. Ask only when the
answer changes the architecture.

| Unknown | Assume | Line to include |
|---|---|---|
| Region | US Commercial `https://api.veracode.com` | "Assuming US Commercial — set `VERACODE_API_BASE` to `api.veracode.eu` / `api.veracode.us` otherwise." (HMAC users: the key-id prefix tells you; see `hmac-and-xml-api.md`) |
| Auth | OAuth 2.0 client credentials for REST scripts; HMAC for wrappers, CI plugins and every XML call | See `reference/auth-and-access.md` |
| Scan type | `STATIC` | "Assuming SAST — say the word for SCA or DAST." |
| Scope | Policy (application level), not sandbox | — |
| CI on `pull_request` | Pipeline Scan | — |
| CI on `push` to main/release | Policy (Upload & Scan) | — |
| Language | Python for scripts, YAML for CI | — |
| Python dependencies | Standard library + `requests` for OAuth; add `veracode-api-signing` only when HMAC is needed | — |

**Genuinely worth asking:** Pipeline vs Policy scan when the phrasing fits both;
whether findings should be Policy- or sandbox-scoped when they named neither;
what artifact they are submitting, if no build step is visible; **whether "the
release scan" means the latest scan in a scope (REST) or a specific named build
(XML)** — they are different architectures.

---

## 4. Invariants — the mistakes that produce no error

These cause *wrong security results*, not exceptions. Repeat them inline as code
comments wherever they apply; do not assume the user will read prose.

1. **`severity` is exact-match. `severity_gte` is the range filter.**
   `?severity=4` returns High **only** and silently drops Very High. For "High and
   above" you must use `severity_gte=4`. The single most damaging error in this API.

2. **There is no top-level `severity` on a finding.** It lives at
   `finding_details.severity` — an **integer** for STATIC, a **string** for SCA.
   Do not compare them with the same operator.

3. **Scale:** `5` Very High · `4` High · `3` Medium · `2` Low · `1` Very Low ·
   `0` Informational. Never send the word `HIGH` to a REST endpoint.
   *Exception:* CI plugin inputs like `fail_on_severity` take English strings
   (`'Very High, High'`). Plugin inputs and API params are different vocabularies —
   do not "correct" one into the other.

4. **SAST and SCA field paths diverge.** STATIC → `finding_details.cwe.id`,
   `.file_path`, `.file_line_number`. SCA → `finding_details.cve.name`,
   `.component_filename`. Reading `cwe` off an SCA finding raises `KeyError`.
   Branch on `finding['scan_type']`.

5. **Findings v2 is context-scoped, not scan-scoped.** It returns the current
   consolidated state of an application or a sandbox — whichever scan ran *last*.
   There is no scan-name or build filter. Findings carry a `build_id`, but
   filtering on it is **not** "state as of that build": it silently drops every
   flaw carried over from earlier scans. Build-scoped results come only from the
   XML `detailedreport.do` (HMAC) — see `hmac-and-xml-api.md`.

6. **Closed findings are returned.** Filter `finding_status.status == 'OPEN'`
   client-side unless the user wants history.

7. **Pagination and empty collections:** loop an integer `page` from `0`, stop
   when `page >= body['page']['total_pages'] - 1`. Do not parse
   `_links.next.href`. Apply this to *every* collection endpoint, sandboxes and
   users included. An empty collection **omits `_embedded` entirely** rather than
   returning `[]` `[v: 2026-09-15 | live]` — use `.get()` at both levels, or a new
   or quiet tenant raises `KeyError`.

8. **Rate limits are per IP:** REST 500/min, XML 250/min, `detailedreport.do`
   80/min. `429` with a wait header. Any portfolio-wide loop needs backoff or it
   will fail partway and look like a permissions problem.

9. **Pipeline Scan results never reach the Findings API.** They are ephemeral and
   local to the CI run. Compliance reporting requires a Policy (Upload & Scan).

10. **Two auth schemes, two credential pairs, both live.** OAuth 2.0 (GA December
    2025) `client_id`/`client_secret` for REST scripts; HMAC API ID/key for the
    official wrappers, every CI plugin's `vid`/`vkey`, and all XML APIs. One
    service account can hold both pairs; they are not interchangeable. An OAuth
    secret in an HMAC signer fails with a "not hexadecimal" error. Do not convert
    a plugin to Bearer tokens.

11. **Never print a signing exception.** `veracode-api-signing` formats the secret
    into its `VeracodeCredentialsError` messages `[v: 2026-10-09 | library source
    26.5.0]`. Catch it and print a fixed message instead.

12. **Count on the composite key.** When an application has several sandboxes
    scanning the same artifact, their findings are identical sets
    `[v: 2026-10-02 | live]`. Dedupe and count on `(app, sandbox, issue_id)` for
    SAST and `(app, sandbox, component, cve)` for SCA — never `issue_id` or
    `cve_id` alone, or "flaws per application" silently doubles.

---

## 5. The mental model

```
Organization
 └─ Business Unit ─ Team ─ User / API service account   [identity.md]
     └─ Application Profile  (REST guid / XML app_id)    [findings-and-annotations.md]
         ├─ Policy           ─ compliance verdict        [policy-and-compliance.md]
         ├─ Policy scope     ─ findings, no ?context=
         └─ Sandbox (guid / sandbox_id) ─ findings, ?context={guid}
              └─ Finding (issue_id)
                   └─ Annotation (comment / mitigation)

Build-scoped view (XML only, HMAC)                       [hmac-and-xml-api.md]
  app_id ─ sandbox_id ─ build_id (version = scan name) ─ detailedreport.do
```

Resolving a human request like "flaws in sandbox X of app Y" is always a chain:

1. `GET /appsec/v1/applications?name={name}` → `application_guid`
   (partial, case-insensitive match — re-check for an exact hit, fail loudly on 0 or >1)
2. `GET /appsec/v1/applications/{guid}/sandboxes` → match `name` → `sandbox_guid`
3. `GET /appsec/v2/applications/{guid}/findings?context={sandbox_guid}`

Never shortcut step 1 by asking the user for a GUID they do not have.

"Flaws in the newest scan *named* X" is a different chain, through the XML APIs:
`getapplist.do` → `getsandboxlist.do` → `getbuildlist.do` (pick by `version`) →
`detailedreport.do`. REST and XML use **different identifiers** (GUIDs vs numeric
ids); staying in one family end to end avoids a mapping this KB has not verified.

Sitting outside this tree: **Pipeline Scan** (ephemeral, CI-local) and
**SCA agent-based scans** (organized by workspace and project, not by application
profile). Do not try to force either into the profile hierarchy.

---

## 6. Output standards

- Complete, runnable code. Credentials and region from env vars, never literals.
- Explicit timeouts. Handle `401` (refresh once) and `429` (sleep, retry).
- Print `issue_id`, `scan_type`, severity and location — enough to debug.
- Put uncertainty at the line it affects, as a comment, not in prose above the
  code block where it will be skimmed past.
- Show the response shape you are indexing into, so the user can diff it against
  reality on the first run.
- When the user's goal implies a scheduled or repeated job, say so and handle
  incrementality — most Veracode integrations are polling loops, and there are
  no webhooks.
- **Make "nothing" provable.** Any extract that can legitimately return zero rows
  (no matching scan, results not ready, genuinely clean) should also write an
  audit/coverage row per application and sandbox saying which it was. On a chart,
  "no release build" and "zero flaws" look identical and mean opposite things.
- **Add a self-check where the data allows one.** Example: each SCA
  `<component>` declares its vulnerability count, so the sum must equal the CVE
  rows written. A mismatch turns a silent parser bug into a loud one.
- Never ask for credentials in chat, and never echo one back. If the user pastes
  a secret, tell them to rotate it.
