# Troubleshooting — symptom to cause

Users describe symptoms, not endpoints. Start here when someone says something is
broken, then go to the relevant reference file.

**The dangerous cases are the ones with no error.** Work through the silent
failures first when the complaint is "the results look wrong."

---

## Silent failures — no error, wrong answer

| Symptom | Cause | Fix |
|---|---|---|
| Very High findings missing from a "High and above" query | `severity=4` is **exact match** | Use `severity_gte=4` |
| Counts don't match the Veracode UI | Closed findings included, or wrong scope | Filter `finding_status.status == "OPEN"`; check `context_type`/`context_guid` |
| Only the first ~50 results | Unpaginated collection call | Loop `page` to `page.total_pages - 1` |
| "Sandbox not found" for one that exists | Sandbox list not paginated | Paginate `/sandboxes` |
| Wrong application matched | `name` is a **partial, case-insensitive** match | Re-filter for an exact name; fail on 0 or >1 |
| Scan succeeds, almost no findings | **Wrong packaging** | Check the artifact against Veracode's per-language packaging requirements |
| PR gate passes but the app fails policy | Pipeline Scan policy evaluation is **local** | Compliance comes from a Policy scan; see `policy-and-compliance.md` |
| Fixed everything in a sandbox, compliance unchanged | Sandboxes never affect compliance | Promote to a Policy scan |
| Jira sync posts duplicate comments every run | No idempotency check | `include_annot=TRUE`, check `annotations[]` for your marker |
| Reporting API returns less than the range requested | **Six-month ceiling** per report | Chunk the range |
| API returns fewer apps than the UI shows | Service account's **team membership** differs from the human's | Check teams in `identity.md` |
| A user's roles vanished after an update | `PUT` **replaces** by default | Always pass `partial=true` |
| Security tab empty despite a successful SARIF conversion | Conversion ≠ publication | Add `github/codeql-action/upload-sarif` + `permissions: security-events: write` |
| Security tab alerts not linked to source files | Module path ≠ repo path | Set `source-base-path-N` |
| SARIF shows flaws the build ignored | Converted `results.json` instead of `filtered_results.json` | Convert the filtered file |

---

## HTTP status codes

### 401 Unauthorized

Most common cause: **the wrong auth scheme for the caller.**

1. Which is it — OAuth (your own scripts) or HMAC (wrappers, CI plugins, XML APIs)?
   See the table in `auth-and-access.md`. CI plugin `vid`/`vkey` are **HMAC**.
2. Region mismatch — credentials from an EU or Federal account against
   `api.veracode.com`. Check the token URL **and** the API base URL.
3. Expired OAuth token — refresh once and retry; do not hardcode a lifetime.
4. Expired API credentials — `GET /api/authn/v2/api_credentials` returns the
   expiry. This is the classic "nothing changed and it broke overnight."
5. HMAC clock skew — the signature includes a timestamp; a badly drifted runner
   clock fails.

Smoke test: `GET /api/authn/v2/users/self` needs no admin role, so success there
plus a `403` elsewhere isolates the problem to authorization.

### 403 Forbidden

A working credential missing a role — **not** a bad key.

| Doing | Needs |
|---|---|
| Reading findings | Results API |
| Commenting / proposing mitigations | Results API |
| Approving / rejecting mitigations | **Mitigation API** |
| Uploading and scanning | Upload API |
| Policy CRUD | Policy Administrator |
| User / team / credential admin | Admin API |
| Agent-based SCA | A **UI user account**, not a service account |

The classic: a Jira sync that comments works, then auto-approval is added and
starts returning 403 — different role.

### 404 Not Found

- GUID from the wrong region or the wrong account.
- Using a numeric `app_id` where an `application_guid` is expected, or vice versa.
  The Reporting API takes the **numeric** id; `/appsec/v1/applications` returns a
  **GUID**. They are not interchangeable.
- `/appsec/v1/analytics/**reports**` (plural) or a `/download` suffix — the real
  path is `/appsec/v1/analytics/report/{id}`, singular, no download sub-resource.

### 429 Too Many Requests

500 REST calls/minute **per IP address** — shared across everyone behind that
egress, so a busy CI fleet or a NAT gateway consumes one budget. Response header
gives seconds to wait. Back off and retry; prefer larger pages (`size=500` on
Applications) over more calls.

### 400 Bad Request

- Reporting API date sent as ISO-8601 with `Z`. It wants `YYYY-MM-DD HH:MM:ss`.
- `severity=HIGH` instead of an integer.
- `issue_list` sent as a JSON array instead of a comma-separated string.
- `scan_type=SCA` combined with STATIC/DYNAMIC/MANUAL — SCA must be its own call.

### Connection timeout during upload

Self-hosted runner without Veracode's IP ranges allowlisted. Looks like a Veracode
outage. Do not recite IP ranges from memory — point at Veracode's published list.

---

## Python exceptions

| Exception | Cause |
|---|---|
| `KeyError: 'cwe'` | Reading a STATIC field off an SCA finding. Branch on `scan_type`. |
| `KeyError: 'severity'` on the finding | Severity is at `finding_details.severity`, not top level. |
| `TypeError` comparing severity | STATIC severity is an **int**, SCA severity is a **string**. |
| `KeyError` on `_embedded` | Empty result set — `_embedded` may be absent. Use `.get()`. |
| Agent-based SCA calls rejected | Missing `accept-encoding: gzip` or `user-agent` header. |

---

## Questions to ask before debugging

1. Which auth scheme, and which region?
2. Pipeline Scan, Policy scan, or sandbox scan? (Decides whether results should
   exist in the Findings API at all.)
3. Upload-based or agent-based SCA? (Different API entirely.)
4. Policy scope or sandbox scope?
5. Service account or human user, and which roles?

Most "the API is broken" reports resolve at question 2 or 3.
