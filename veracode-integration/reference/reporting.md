# Reporting (Analytics) API — BI, SIEM and bulk extraction

**Traps in this file:** the path is `/analytics/**report**`, singular · there is
no `/download` sub-resource · dates are `YYYY-MM-DD HH:MM:ss`, not ISO-8601 with
`Z` · **maximum six months of data per report** · `app_id` here is the numeric ID,
not the `application_guid`.

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

## Six-month ceiling

A single report returns at most **six months** of data. Longer ranges must be
chunked, and the chunking is the caller's job — the API will not warn you, it
will just return less than you asked for. Any backfill script needs a loop over
six-month windows.

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

## Auth

Veracode's examples use HMAC (`--auth-type=veracode_hmac`). OAuth works for REST
generally; if a Reporting call `401`s under OAuth while other calls succeed, that
is worth flagging to the user rather than assuming a code bug.

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
| Results for one specific build | **Neither** — legacy XML `detailedreport.do` |

Common production pattern: nightly `FINDINGS` report with
`last_updated_start_date` = last successful run, then the Findings API for detail
on just the applications that appear in the delta. This is also how you keep a
Jira sync inside the rate limit.

## Scheduling and operations

- Store the last successful `last_updated_start_date` and resume from it; overlap
  by a few minutes rather than risking a gap.
- Reports are asynchronous — do not run them inside a request/response cycle.
- Six-month ceiling plus polling means a first-time backfill is a batch job, not
  a script run interactively.
- The numeric `app_id` comes from the legacy app identifier, not
  `/appsec/v1/applications`' `guid`. If a user has GUIDs and needs numeric IDs,
  that mapping is **unverified** here — flag it rather than inventing a lookup.
