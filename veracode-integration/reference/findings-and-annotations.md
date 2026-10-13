# Applications, Sandboxes, Findings and Annotations

**Traps in this file:** `severity` is exact-match (use `severity_gte`) ·
severity lives at `finding_details.severity`, int for STATIC and string for SCA ·
closed findings are returned by default · `include_annot=TRUE` is what makes a
ticket sync idempotent · app `name` search is a partial match · an empty
collection has no `_embedded` key at all · findings cannot be filtered to a build
or scan name.

---

## Applications `[v: 2026-09-15 | docs.veracode.com/r/c_apps_intro]`

`GET /appsec/v1/applications?name={name}&page={n}&size={n}`

- `name` — **partial, case-insensitive**. Always re-filter for an exact match and
  fail loudly on 0 or >1 hits. "Payment-Gateway" also matches
  "Payment-Gateway-Legacy".
- `page` default 0; `size` default 50, **max 500**.
- Response: `_embedded.applications[].guid`, `.profile.name`,
  `.profile.business_criticality`.
- **The compliance verdict is already here:**
  `profile.policies[].policy_compliance_status` (e.g. `DID_NOT_PASS`) plus
  `last_policy_compliance_check_date` `[v: 2026-09-18 | live]` — see
  `policy-and-compliance.md`. A portfolio compliance view needs no per-app call.

### Filters `[v: 2026-09-15 | live]`

`page`, `size`, `org`, `name`, `policy_id`, `policy_guid`, `legacy_id`,
`business_unit`, `tag`, `policy`, `policy_compliance`, `scan_status`,
`scan_type`, `modified_after`, `policy_compliance_checked_after`, `team`,
`git_repo_url`, `custom_field_names`, `custom_field_values`,
`sort_by_custom_field_name`.

`legacy_id` looks up an application by its numeric XML-API `app_id` — useful
when joining REST metadata onto XML build-scoped results. That the two ids are
the same number in every tenant is **unverified**; spot-check one.

### Visibility

An account without the `noteamrestrictionapi` role sees only the applications
its teams can see. A short list that *looks* complete is the usual symptom — see
`auth-and-access.md`.

Other documented operations (`GET /{guid}`, `POST`, `PUT`, `DELETE`) exist;
request bodies for profile creation are **unverified** here — check the
Applications spec.

## Sandboxes `[v: 2026-09-15 | docs.veracode.com/r/c_sandbox_create_rest]`

- `GET  /appsec/v1/applications/{application_guid}/sandboxes`
  → `_embedded.sandboxes[].guid`, `.name`
- `POST /appsec/v1/applications/{application_guid}/sandboxes` — body `{"name": "..."}`
- `PUT  /appsec/v1/applications/{application_guid}/sandboxes/{sandbox_guid}`

**Paginate the list.** A busy application has many sandboxes; an unpaginated
lookup returns "sandbox not found" for one that exists, which reads as a name
typo and wastes a lot of debugging.

---

## Findings v2

`GET /appsec/v2/applications/{application_guid}/findings`

### Query parameters `[v: 2026-09-15 | docs.veracode.com/r/c_findings_v2_examples + Findings OpenAPI model]`

| Param | Type | Notes |
|---|---|---|
| `context` | string | **Sandbox GUID.** Omit for Policy scope. |
| `scan_type` | array of string | `STATIC` · `DYNAMIC` · `MANUAL` · `SCA`. Repeatable. SCA cannot be combined with the others. |
| `severity` | int 0–5 | **EXACT match.** |
| `severity_gte` | int 0–5 | **Greater than or equal.** Almost always the one you want. |
| `violates_policy` | bool | `TRUE` / `FALSE` |
| `include_annot` | bool | `TRUE` adds `annotations[]` to each finding |
| `include_exp_date` | bool | Adds `grace_period_expires_date` |
| `new` | bool | Findings new in the most recent scan |
| `mitigated_after` | date-time | Findings mitigated after this timestamp |
| `cwe` | array of int | e.g. `cwe=80` |
| `finding_category` | array of int | |
| `cve` | string | SCA |
| `cvss` / `cvss_gte` | number | SCA |
| `sca_scan_mode` / `sca_dep_mode` | string | SCA; enum values **unverified** |
| `page` / `size` | int | Standard pagination |

### Envelope `[v: 2026-09-15 | Findings OpenAPI model]`

```jsonc
{
  "_embedded": { "findings": [ /* Finding */ ] },
  "_links": { },
  "page": { "number": 0, "size": 50, "total_elements": 137, "total_pages": 3 }
}
```

This envelope shape (`_embedded.<collection>` + `page.*`) is consistent across
`/appsec` collection endpoints. **When the collection is empty, `_embedded` is
omitted entirely** — not an empty array `[v: 2026-09-15 | live]`:

```python
items = body.get("_embedded", {}).get("findings", [])   # both levels, always
```

The collection key is not always the resource name: `/appsec/v1/policies`
returns `_embedded.policy_versions` `[v: 2026-09-15 | live]`. Print the first
response from any collection endpoint you have not used before.

### Finding object `[v: 2026-09-15 | Findings OpenAPI model]`

```jsonc
{
  "issue_id": 1001,               // int64 — the ID the Annotations API takes
  "scan_type": "STATIC",
  "description": "...",
  "count": 1,
  "context_type": "APPLICATION",  // or SANDBOX
  "context_guid": "…",
  "violates_policy": true,
  "build_id": 123456,
  "grace_period_expires_date": "…",   // only with include_exp_date
  "finding_status": {
    "status": "OPEN",                  // OPEN | CLOSED
    "resolution": "…",
    "resolution_status": "NONE",       // NONE | PROPOSED | APPROVED | REJECTED
    "mitigation_review_status": "…",
    "new": true,
    "first_found_date": "…",
    "last_seen_date": "…"
  },
  "finding_details": { /* varies by scan_type */ },
  "annotations": [                     // only with include_annot=TRUE
    { "action": "COMMENT", "comment": "…", "created": "…", "user_name": "…",
      "remaining_risk": "…", "specifics": "…", "technique": "…",
      "verification": "…" }
  ]
}
```

**No top-level `severity`.** It is inside `finding_details`.

### `finding_details` by scan type `[v: 2026-09-15 | Findings OpenAPI model]`

**STATIC** — `severity` (**int 0–5**), `cwe.{id,name,href}`, `file_path`,
`file_name`, `file_line_number`, `module`, `procedure`, `relative_location`,
`exploitability`, `attack_vector`, `cvss`, `finding_category.{id,name}`

**SCA** — `severity` (**string**), `cve.{name,cvss,severity,href}`, `cwe`,
`component_filename`, `component_id`, `component_path[]`, `product_id`,
`version`, `language`, `licenses[]`, `metadata`

**DYNAMIC / MANUAL** — separate schemas, **not captured here.** Say so and point
at the Findings spec.

### Deeper flaw detail

- `GET /appsec/v2/applications/{guid}/findings/{issue_id}/static_flaw_info`
  — module, file path, function, line numbers, call stack
- `GET /appsec/v2/applications/{guid}/findings/{issue_id}/dynamic_flaw_info`
  — request/response and attack vector

`[v: 2026-09-15 | docs.veracode.com/r/c_rest_static_finding_data_path_intro]`
Exact response schemas **unverified**.

---

## Annotations

`POST /appsec/v2/applications/{application_guid}/annotations`
`[v: 2026-09-15 | docs.veracode.com/r/c_annotations_add_comment_rest, /r/c_annotations_propose_mitigation_rest, /r/c_annotations_approve_mitigation_rest]`

```json
{ "issue_list": "1001,1002", "comment": "Ticket created: PROJ-123", "action": "COMMENT" }
```

All three fields required. `issue_list` is a **comma-separated string**, not a
JSON array — a common and silent mistake.

### Actions

| Action | Effect |
|---|---|
| `COMMENT` | Adds a comment. Does **not** change `resolution_status`. |
| `FP` | Propose false positive |
| `APPDESIGN` | Propose mitigation by application design |
| `NETENV` | Propose mitigation by network environment |
| `OSENV` | Propose mitigation by OS environment |
| `LIBRARY` | Propose — library not maintained by this team |
| `ACCEPTRISK` | Propose risk acceptance |
| `ACCEPTED` | Approve a proposed mitigation |
| `REJECTED` | Reject a proposed mitigation |

Lifecycle: propose (`resolution_status` → `PROPOSED`) → `ACCEPTED` / `REJECTED`
by a different, more privileged account.

`veracode-api-py` exposes aliases (`POTENTIAL_FALSE_POSITIVE`, `APP_BY_DESIGN`,
`OS_ENV`, `NET_ENV`, `ACCEPT_RISK`) and maps them. **The raw REST API takes the
short forms above.** If a user's code has the long forms, they are on the wrapper.

### Roles

Comments/proposals: `Results API` (service account) or Reviewer / Security Lead
(UI). Approve/reject: `Mitigation API` or Mitigation Approver. A `403` here is a
role problem — see `auth-and-access.md`.

### ⚠ Sandbox scoping — unresolved

Veracode's public annotation doc pages show **no `context` parameter**, yet
`veracode-api-py`'s `add_annotation()` accepts a `sandbox` guid. The wire
parameter name is **unverified**.

**Tell the user this rather than guessing.** Safe path: annotate Policy-scope
findings, or confirm against the Annotations spec before shipping a
sandbox-scoped sync.

### Undocumented limits

Comment maximum length, maximum `issue_list` size per call, success status code
and response body are all **undocumented**. Chunk conservatively (~50 IDs), keep
comments short, and do not assert a limit you cannot cite.

### Idempotency — the thing that makes a sync real

There is no `GET /annotations`. You read existing annotations by adding
`include_annot=TRUE` to the **findings** query, then checking `annotations[]` for
your own marker before posting again. Without this, every run posts a duplicate
comment forever. See `recipes.md` §2.

### SCA annotations

SCA findings are annotated through a separate SCA Annotations API. Path and
schema **unverified** — do not assume the `/appsec/v2/.../annotations` endpoint
accepts SCA `issue_id`s.

---

## What Findings v2 cannot do

- **No scan or build selector.** `?context=` gives a sandbox's current
  consolidated state, which reflects whichever scan ran last. If release and
  branch builds share a sandbox, that state flips depending on which one scanned
  last. "Findings from the newest scan named *release*" is an XML job
  (`hmac-and-xml-api.md` §6).
- **Do not filter on `build_id`** to fake it. A consolidated finding's `build_id`
  is not "state as of that build"; filtering on it silently drops every flaw
  carried over from earlier scans. It looks right on a small sample and is wrong
  at scale. Use it only as an informational "carried over from an earlier build"
  flag.
- **No closed date and no "as of" parameter.** Per-finding `first_found_date` /
  `last_seen_date` exist, but you cannot reconstruct last month's portfolio state
  from a current-state API. Trend needs snapshots you keep, or the Reporting API.
- **Several sandboxes, same artifact = identical finding sets** `[v: 2026-10-02 |
  live]`. Summing per application double counts. Key on
  `(application, context_guid, issue_id)`.

## Incremental sync

The Findings API has **no "updated since" filter** and there are **no webhooks**.
Every integration is a polling loop. For large portfolios, drive the incremental
set off the Reporting API's `last_updated_start_date` (see `reporting.md`) and use
the Findings API only for detail on what changed.

`issue_id` uniqueness across Policy and Sandbox scope is **not documented**. Key
external records on `(context_guid, issue_id)`, never `issue_id` alone.
