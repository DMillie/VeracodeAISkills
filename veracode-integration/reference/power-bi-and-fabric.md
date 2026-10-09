# Power BI, Power Query and Microsoft Fabric

**Traps in this file:** Power Query has no HMAC, so the XML APIs are unreachable
from it · Power Query cannot poll, so the Reporting API is unreachable from it ·
per-application URLs that refresh in Desktop **fail in the Power BI Service** ·
the browser editor cannot create parameters · the verdict enum has underscores.

Everything here was hit for real while building a Veracode → Power BI proof of
concept on Power BI Pro, browser-only `[v: 2026-09-18 | live]` unless tagged
otherwise.

---

## The line that matters is depth of detail, not data volume

A hundred applications is a few hundred API calls — volume is rarely the
constraint. The real line is **what level of detail** the dashboard needs.

| Tier | What it shows | How | Infrastructure |
|---|---|---|---|
| **1 — portfolio posture** | Compliance rate; verdict breakdown (passed / conditional / did not pass / not assessed); apps failing and never assessed; scan coverage and recency; slicing by business unit, criticality, team, policy | **One** static URL: `GET /appsec/v1/applications` (paginated). It already carries the verdict (`policy-and-compliance.md`) | Pure Power Query, Pro, browser. Works today |
| **2 — finding detail** | Severity breakdown, CWE categories, SCA components, ageing, grace-period clock | Findings v2 per application, or XML for build-scoped data | Something other than Power Query must make the HTTP calls |
| **3 — trend / build-scoped** | History over time, "findings in the latest *release* scan", portfolio delta | Reporting API (needs polling) or XML `detailedreport.do` (needs HMAC) | Fabric notebook/pipeline, or an external extractor |

Lead with Tier 1 — it demos immediately — and present Tier 2/3 as the same
dashboard with more pages once an extractor is scheduled.

## Why Power Query stops at Tier 1 in the Service

### Per-application URLs fail on refresh

`Findings` builds its URL from data (`"appsec/v2/applications/" & [Guid] & "/findings"`).
In Desktop, `Web.Contents(base, [RelativePath = ...])` keeps that from counting
as a dynamic data source. **In the Service it does not.** Refresh registers each
resolved URL as its own data source:

```
The credentials provided for the Web source are invalid.
(Source at https://api.veracode.com/appsec/v2/applications/<guid>/findings.)
```

One data source per application GUID. This is the documented dynamic-data-source
limitation, not a configuration error. The documented fix is an on-premises data
gateway — Windows-only.

The errors on the way there, in the order they appear:

1. `DMTS_DatasourceHasNoCredentialError` — data-source detection is **static**:
   any host named in the M text needs a credential, even if a sample-data switch
   means it is never called.
2. `Formula.Firewall` / "specify a privacy level" — set the source's privacy level
   to Public in the Service (the Desktop "ignore privacy levels" option does not
   exist in the browser).
3. "Credentials provided for the Web source are invalid" on a per-app URL — the
   actual wall above.

### No HMAC, no polling

- **No HMAC-SHA256 primitive in M.** Everything XML (build-scoped results,
  scan-name selection) is out of reach. OAuth (GA December 2025) is what makes
  Tier 1 possible at all.
- **No polling.** M has no mutable state, no sleep and no loop-until, so the
  asynchronous Reporting API (submit → poll → fetch) cannot be driven from Power
  Query or Dataflow Gen2 (same engine). On Pro, Fabric is the only route to
  polling — and therefore to a trend line.
- **Current state only.** Synchronous endpoints return now, not history; nothing
  in Power BI accumulates snapshots across refreshes.

### The browser editor (Power BI Service, no Desktop)

Desktop is Windows-only, so macOS users build in the browser `[v: 2026-09-15 | live]`:

- **Cannot create parameters** (edit only). Use a `Config` query returning a
  record and reference its fields.
- **`Web.Contents`'s first argument must be a literal string.** A `Config` field
  counts as computed. Hardcode the base URL in each function that calls the API,
  and change every copy for `.eu` / `.us`.
- No auto-detected relationships (define them by hand), no external tools
  (Tabular Editor, DAX Studio), no incremental refresh, no PBIP.
- Pro: 8 refreshes/day, and no Key Vault — the secret lives in the semantic model.

## Power Query patterns that do work

```m
// Token: client credentials, literal base URL (required in the browser).
fnGetToken = () =>
    let
        basic = Binary.ToText(Text.ToBinary(Config[ClientId] & ":" & Config[ClientSecret]), BinaryEncoding.Base64),
        resp  = Json.Document(Web.Contents("https://api.veracode.com",
                    [RelativePath = "api/authn/v2/oauth2/token",
                     Headers = [Authorization = "Basic " & basic,
                                #"Content-Type" = "application/x-www-form-urlencoded"],
                     Content = Text.ToBinary("grant_type=client_credentials")]))
    in
        resp[access_token]
```

- `_embedded` is omitted on an empty collection — use
  `Record.FieldOrDefault(Record.FieldOrDefault(body, "_embedded", []), "applications", {})`.
- Paginate with `List.Generate` over `page` until `page.total_pages`.
- Severity is an int for STATIC and a string for SCA — normalise through one
  helper before any measure touches it.
- Verdicts are `DID_NOT_PASS` style. `Text.Contains(s, "DID NOT PASS")` never
  matches; replace underscores first or compare to the enum.
- A `Config[UseSampleData]` switch that swaps every table for inline sample rows
  with identical column names lets the model and report be built before
  credentials or scans exist.

## Tier 2 and 3 — choose where the HTTP calls happen

| Option | Fits when | Notes |
|---|---|---|
| **External extractor** (recommended default) | Pro only, macOS, today | Python on a schedule (cron, container, CI job) writes CSV/Parquet to SharePoint/OneDrive; Power BI imports one static file URL. Can use OAuth (REST) or HMAC (XML). See `recipes.md` |
| **Fabric notebook / Data Pipeline** | Fabric capacity (F2+) or the trial | Python with `veracode-api-signing` → HMAC and XML; a notebook loop or pipeline `Until` activity → Reporting API polling; Key Vault via `notebookutils.credentials.getSecret`; append-only Lakehouse tables + Direct Lake = history with no refresh cycle |
| **On-premises gateway** | Windows host available | The documented fix for dynamic sources; worst option for a macOS user |

### Extract shape that keeps the model honest

- Flaws, SCA components and SCA CVEs as **separate tables** (component is
  inventory, CVE is the finding), plus an **audit/coverage table** with one row
  per application and sandbox and an outcome for each.
- Keep `app`, `sandbox`, `scan_name`, `build_id` on every finding row.
- **Dedupe on the composite key** — `(app, sandbox, issue_id)` for SAST,
  `(app, sandbox, component, cve_id)` for SCA. Several sandboxes scanning the same
  artifact produce identical sets `[v: 2026-10-02 | live]`; a "flaws per
  application" measure that sums rows double-counts. Default the report to slicing
  by sandbox, or use an explicit `DISTINCTCOUNT` over the composite key.
- For SCA, export `found_after_scan` so a CVE published after the release scan
  is not read as "shipped knowing this" (`hmac-and-xml-api.md` §8).

### Design ceiling

One paginated findings call per application at 500 REST calls/minute **per IP**
puts a synchronous design at roughly 150–200 applications. Past that, move to
the Reporting API (polling, so not Power Query) or XML with pacing.
