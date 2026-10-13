# Reporting (Analytics) API — BI, SIEM and bulk extraction

**Traps in this file:** the path is `/analytics/**report**`, singular · there is
no `/download` sub-resource · dates are `YYYY-MM-DD HH:MM:ss`, not ISO-8601 with
`Z` · **the start date must be within the last six months**, so there is no
backfill beyond that · it validates the request before checking authorization, so
a `400` proves nothing about access · `app_id` here is the numeric ID, not the
`application_guid` · Power Query cannot use this API at all (it cannot poll).

Use this — not the Findings API — whenever the scope is "the whole portfolio" or
"everything that changed since last night." Looping the Findings API across
hundreds of applications will hit the 500/min rate limit and take hours.

---

## Endpoints `[v: 2026-09-15 | docs.veracode.com/r/Reporting_REST_API]`

```
POST /appsec/v1/analytics/report          -> { "id": "<report_id>", ... }
GET  /appsec/v1/analytics/report/{id}     -> poll, then returns the data
```

Singular `report`. There is **no** `/appsec/v1/analytics/reports` and **no**
`/{id}/download`.

## Report types

`FINDINGS` · `SCANS` · `DELETEDSCANS` · `AUDIT`

### FINDINGS

```jsonc
{
  "report_type": "FINDINGS",
  "last_updated_start_date": "2026-01-01 00:00:00",
  "last_updated_end_date":   "2026-02-01 00:00:00",   // optional
  "app_id": 12345,                 // optional — NUMERIC app id, not the GUID
  "scan_type": ["Static Analysis"],// optional
  "policy_sandbox": "Policy",      // "Policy" | "Sandbox"
  "policy_rule_passed": "yes",     // "yes" | "no"
  "status": "open",                // open | closed | mitigated
  "severity": [4, 5],              // optional array
  "custom_severity": [4, 5]        // optional array
}
```

### SCANS

```jsonc
{
  "report_type": "SCANS",
  "last_updated_start_date": "2026-01-01",
  "last_updated_end_date": "2026-02-01",   // optional
  "app_id": 12345,                          // optional
  "policy_sandbox": "policy",               // optional
  "scan_type": ["Static Analysis"],         // optional
  "most_recent_scan": true                  // optional
}
```

### DELETEDSCANS

```jsonc
{
  "report_type": "DELETEDSCANS",
  "deletion_start_date": "2026-01-01",
  "deletion_end_date": "2026-02-01",   // optional
  "scan_type": ["Static Analysis"],    // optional
  "policy_sandbox": "policy",          // optional
  "app_id": 12345                      // optional
}
```

### AUDIT

```jsonc
{
  "report_type": "AUDIT",
  "start_date": "2026-01-01",
  "end_date": "2026-02-01",                 // optional
  "audit_action": ["Delete", "Create", "Update"],  // optional
  "action_type": ["Login", "Admin"],        // optional
  "target_user_id": [123],                  // optional
  "modifier_user_id": [456]                 // optional
}
```

## Dates

Accepted: `YYYY-MM-DD` and `YYYY-MM-DD HH:MM:ss`. **Not ISO-8601 with `Z`** — a
`2026-01-01T00:00:00Z` value is rejected.

Omitted time defaults to `00:00:00.000`, so to cover a whole day use the *next*
date as the end: all of October 2026 is start `2026-10-01`, end `2026-11-01`.

## Six-month window — enforced from today

`[v: 2026-09-15 | live]` The server rejects any start date older than six months
**before today**, not merely ranges longer than six months:

```
400  [last_updated_start_date must be (0-6 months) before today's date]
```

Consequences:

- **No historical backfill past six months.** Chunking an old range into
  six-month windows does not help; every window's start must be recent.
- A report covers findings **updated** in the window. A finding untouched for
  seven months does not appear, even if it is still open.
- If a customer needs a longer trend, start accumulating now: run the report on
  a schedule and append to your own store. History only exists from the day the
  job is switched on.
- Within the window, the API will not warn about anything it leaves out. Keep
  the last successful `last_updated_start_date` and resume from it.

## Polling

Status values and the exact response/data envelope are **unverified**. The
documented flow is POST → take `id` → GET until the data is present.

Write polling defensively and say so in the code:

```python
def run_report(vc, body, api_base, poll_s=10, timeout_s=900):
    rid = vc.post(f"{api_base}/appsec/v1/analytics/report", json=body)["id"]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = vc.get(f"{api_base}/appsec/v1/analytics/report/{rid}")
        # Status field name and values are UNVERIFIED in this KB.
        # Print `resp` on the first run and pin the real condition.
        status = str(resp.get("status", "")).upper()
        if status in ("COMPLETED", "COMPLETE"):
            return resp
        if status in ("FAILED", "ERROR"):
            raise RuntimeError(f"Report {rid} failed: {resp}")
        time.sleep(poll_s)
    raise TimeoutError(f"Report {rid} not ready after {timeout_s}s")
```

Do not present a polished status enum as fact. Tell the user to inspect the first
response and pin the condition.

## Auth and access

Veracode's examples use HMAC (`--auth-type=veracode_hmac`). OAuth works for REST
generally; if a Reporting call `401`s under OAuth while other calls succeed, that
is worth flagging to the user rather than assuming a code bug.

**Role:** `reportingApi` on an API service account. Without it the call returns
`403 "Account is not authorized to access the API"` `[v: 2026-09-15 | live]`.

**Validation runs before authorization** `[v: 2026-09-15 | live]`. A malformed
date returns `400` even for an account entitled to nothing. Do not read a `400`
as proof that access works — only a `200` with a report `id` does.

---

## Choosing between Reporting and Findings

| Need | Use |
|---|---|
| One app or sandbox, current state, full flaw detail | Findings API |
| Whole portfolio, or "what changed since X" | Reporting API |
| Scan history and cadence | Reporting API, `SCANS` |
| Who changed what, compliance audit | Reporting API, `AUDIT` |
| Feeding Power BI / Splunk / Snowflake on a schedule | Reporting API |
| Detail for a specific `issue_id` | Findings API |
| Results for one specific build or scan name | **Neither** — legacy XML `detailedreport.do` (`hmac-and-xml-api.md`) |
| A PDF for an auditor or an application owner | Custom PDF API (below), or XML `detailedreportpdf.do` for a sandbox build |
| A dashboard in Power BI | See `power-bi-and-fabric.md` before choosing — Power Query cannot poll this API |

Common production pattern: nightly `FINDINGS` report with
`last_updated_start_date` = last successful run, then the Findings API for detail
on just the applications that appear in the delta. This is also how you keep a
Jira sync inside the rate limit.

## Scheduling and operations

- Store the last successful `last_updated_start_date` and resume from it; overlap
  by a few minutes rather than risking a gap.
- Reports are asynchronous — do not run them inside a request/response cycle.
- A first run can reach back six months at most; set that expectation before the
  customer asks for "the last two years".
- The numeric `app_id` comes from the legacy app identifier, not
  `/appsec/v1/applications`' `guid`. The applications list carries a numeric `id`
  and accepts a `legacy_id` filter, but that these equal this API's `app_id` is
  **unverified** — spot-check one before relying on it.

---

## Custom PDF ("Customizable Report") API

`[v: 2026-10-02 | docs.veracode.com/r/c_custom_pdf_api, SwaggerHub
Veracode/custom-pdf-report-api/1.0.0, veracode-api-py 0.9.68 source]`
**Not yet run against a live tenant.**

Produces the same PDF as Reports → "Customizable Report (PDF)" in the platform.
It is a PDF, so it does **not** feed a BI tool.

### Flow (asynchronous)

```
POST https://api.veracode.com/report/pdf        -> { request_id, status: "SUBMITTED", ... }
GET  https://api.veracode.com/report/pdf/{id}   -> { status: ACCEPTED | COMPLETE | CANCELLED | ERROR,
                                                     downloadUrl (when COMPLETE) }
GET  {downloadUrl}                              -> the PDF (relative: /plm/v1/report/pdf/async/{uuid}/pdf?appName=...)
```

`api.veracode.com` and `api.veracode.eu` only — **not available in FedRAMP**.
How long `downloadUrl` stays valid is undocumented ("a limited period"); download
promptly.

### Scope: the application profile only

The request has **no sandbox, context, build or scan selector** — only `app_id`
(the **numeric** id, not the GUID) and section flags. Whether an unknown field
such as `sandbox_id` is rejected or silently ignored is untested; do not tell
anyone a sandbox PDF "works" this way. For sandbox results as a PDF, use the XML
`detailedreportpdf.do` / `summaryreportpdf.do` with the sandbox build's
`build_id` — the standard Detailed Report layout, one build, HMAC only.

### Request body

The API defaults differ from the UI's, so **send every field explicitly**.

| Field | Type | API default | UI label |
|---|---|---|---|
| `app_id` | int, **required** | — | numeric app id |
| `scan_types` | array: `Static`, `Dynamic`, `Manual`, `SCA` | `["Static"]` | Scan Type Selection |
| `executive_summary` | bool | true | Executive Summary |
| `policy_evaluation` | bool | true | Policy Evaluation |
| `findings_impacting_policy` | bool | true | "Only findings that impact policy" *(mapping inferred)* |
| `findings_severity_level` | `all` · `very_high` · `high` · `medium` · `low` · `very_low` | `all` | severity dropdown *(mapping inferred)* |
| `findings_summary` | bool | true | Findings Summary |
| `flaw_category_details` | bool | true | Flaw Category Details |
| `findings_details` | bool | true | Findings Details |
| `sca_vulnerability_details` | bool | true | SCA Findings Details |
| `changes_from_last_scan` | bool | true | Changes From Last Scan |
| `static_scan_details` | bool | true | Static Scan Details |
| `dynamic_scan_details` | bool | false | DAST accounts only |
| `penetration_test_summary` | bool | false | manual pen test accounts only |
| `proposed_mitigated_findings` / `approved_…` / `rejected_…` | bool | true | Mitigations |
| `sca_standalone` | bool | false | none — spec says only "SCA standalone mode" |
| `veracode_methodology` | bool | **false** | Veracode Methodology (**checked** in the UI) |

Unverified: how `findings_impacting_policy` combines with
`findings_severity_level`; whether `high` means "High and above"; whether the
applications list's numeric `id` is this API's `app_id`.

### Auth and roles

Public docs show HMAC only; OAuth on this endpoint is untested. A `401` here while
the same token works on `/appsec/v1/applications` means the API does not take
OAuth — fall back to HMAC. The spec also lists an `X-AUTH-TOKEN` header; it looks
like the internal service's own scheme behind the gateway, so callers should not
send it. Needs **Results API** (service account) or Executive / Reviewer /
Security Lead (UI user), team access to the app, and at least one published scan.
