# Authentication, roles and rate limits

**Traps in this file:** two live auth schemes with two different credential
pairs that are not interchangeable · wrappers, CI plugins and every XML call are
HMAC-only · a human user cannot hold API roles · a `403` is almost always a
missing role, not a bad credential.

---

## Which scheme for which caller

| Caller | Scheme |
|---|---|
| Your own Python/Node/Go REST script | **OAuth 2.0 client credentials** |
| `veracode-api-py`, Java API wrapper, `httpie --auth-type=veracode_hmac` | **HMAC** |
| GitHub Actions / Jenkins / GitLab / Azure DevOps plugins (`vid`/`vkey`) | **HMAC** |
| Pipeline Scan JAR or Docker image | **HMAC** |
| Legacy XML APIs (`analysiscenter.veracode.*`, `*.do`) — build-scoped results, Upload & Scan | **HMAC only** |
| Power Query (Power BI, Dataflows) | **OAuth only** — M has no HMAC-SHA256 primitive |
| Postman | Either — HMAC via a pre-request script (`hmac-and-xml-api.md` §4) |

Getting this wrong is the most common `401`. Ask which one they are on before
debugging anything else.

### Two credential pairs, not one

| | HMAC | OAuth |
|---|---|---|
| Pair | API ID + API key (hex) | `client_id` + `client_secret` |
| Env vars | `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET` | `VERACODE_CLIENT_ID` / `VERACODE_CLIENT_SECRET` |
| Wrong one in the slot | OAuth secret in an HMAC signer → `does not seem to be hexadecimal` / `Non-hexadecimal digit found` `[v: 2026-10-02 | live]` | HMAC key as a client secret → `401` from the token endpoint |

One service account can hold both. When someone says "my Veracode credentials",
find out which pair before writing auth code. Full HMAC detail — signing,
region prefixes, Postman — is in `hmac-and-xml-api.md`.

---

## OAuth 2.0 client credentials `[v: 2026-09-15 | docs.veracode.com/r/OAuth_Client_credentials, /r/c_api_credentials3]`

GA since **December 2025**. Before that Veracode supported HMAC only — models
trained earlier will insist OAuth does not exist. It does.

```http
POST https://api.veracode.com/api/authn/v2/oauth2/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

Response carries `access_token`; send it as `Authorization: Bearer <token>` on
every subsequent request. Regional: replace `veracode.com` with `veracode.eu` or
`veracode.us` — in the token URL *and* the API base URL.

```python
import base64, os, requests

def get_token(base=os.getenv("VERACODE_API_BASE", "https://api.veracode.com")):
    basic = base64.b64encode(
        f"{os.environ['VERACODE_CLIENT_ID']}:{os.environ['VERACODE_CLIENT_SECRET']}"
        .encode()).decode()
    r = requests.post(
        f"{base}/api/authn/v2/oauth2/token",
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        data="grant_type=client_credentials", timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]
```

- Scope follows the **roles on the service account**, not a `scope` parameter.
- Token lifetime: `expires_in: 3599`, `token_type: Bearer`
  `[v: 2026-09-15 | live]` (the Identity spec says 3600). Still do not hardcode
  it: cache until shortly before `expires_in`, and refresh on `401` and retry once.
- Creating and rotating OAuth clients (including for a service account without
  logging in as it) is in `identity.md`.
- Advantages Veracode cites over HMAC: expiring credentials, narrower permission
  scoping.

## HMAC `[v: 2026-10-09 | veracode-api-signing 26.5.0]`

```
Authorization: VERACODE-HMAC-SHA-256 id=...,ts=...,nonce=...,sig=...
```

Do not hand-roll the signature in Python. Use Veracode's `veracode-api-signing`:

```python
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

r = requests.get(f"{base}/appsec/v1/applications",
                 auth=RequestsAuthPluginVeracodeHMAC(), timeout=60)
```

It reads `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET`, then
`~/.veracode/credentials` (profile from `VERACODE_API_PROFILE`, default
`default`):

```ini
[default]
veracode_api_key_id = <id>
veracode_api_key_secret = <secret>
```

For `httpie`: `http --auth-type=veracode_hmac GET "<url>"`. Veracode's own doc
examples are written this way — when you copy one, remember the reader may be on
OAuth.

Region prefixes, the regional XML hosts, the exception that leaks the secret,
non-Python signers and the XML APIs themselves: `hmac-and-xml-api.md`.

### HMAC credential lifecycle `[v: 2026-10-09 | docs.veracode.com/r/HMAC_credentials]`

- One active pair per user. Generating a new pair revokes the old one **24 hours
  later** — the rotation grace window.
- Pairs expire after **one year** (organization maximum). Expiry is the classic
  "nothing changed and the pipeline broke overnight".

## Environment variables

| Variable | Used by |
|---|---|
| `VERACODE_CLIENT_ID` / `VERACODE_CLIENT_SECRET` | OAuth |
| `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET` | HMAC |
| `VERACODE_API_PROFILE` | HMAC: which profile in `~/.veracode/credentials` |
| `VERACODE_API_BASE` | Region (your own convention — set it explicitly) |

Never hardcode credentials, never log a token, never echo a secret in CI.

---

## Roles — what a `403` means

`403` on a working credential is a missing role, not a bad key. Relevant ones
`[v: 2026-09-15 | docs.veracode.com/r/c_rest_annotations_intro, /r/c_API_roles]`:

| Action | API service account role | UI user role |
|---|---|---|
| Read findings / results | Results API | Reviewer, Security Lead |
| Add comments, propose mitigations | Results API (wrapper docs: *Mitigation and Comments API*) | Reviewer, Security Lead |
| Approve / reject mitigations | Mitigation API | Mitigation Approver |
| Upload and scan | Upload API | Submitter |
| Create / update policies | — | Policy Administrator |
| Manage users, teams, credentials | Admin API | Administrator |
| See every application regardless of team | **No Team Restriction API** | (team membership) |
| Reporting (Analytics) API | Reporting API | — |
| Customizable PDF report | Results API | Executive, Reviewer, Security Lead |

### Exact API role names `[v: 2026-09-15 | live]`

The 14 API roles, as the Identity API names them (`role_name`):

`adminapi` · `apisubmitanyscan` · `apisubmitdynamicanalysis` ·
`apisubmitdynamicscan` · `apisubmitstaticscan` · `archerreports` ·
`extunifiedstaticscanuser` · `greenlightapiuser` · `mitigationapi` ·
`noteamrestrictionapi` · `reportingApi` · `resultsapi` · `submitterapi` ·
`uploadapi`

The table above uses the display names (`role_description`, e.g. "Results API").
Creating an OAuth client takes roles as `[{"role_description": "Results API"}]`.

A sensible read-only reporting account: `resultsapi` + `noteamrestrictionapi`
(add `reportingApi` for the Analytics API, `uploadapi` only if it must also submit
scans). Without `noteamrestrictionapi`, the account sees only its teams'
applications and the extract looks complete when it is not.

**API roles go on API service accounts only.** Assigning one to a human user
returns `400 "Cannot assign API roles to human user"` `[v: 2026-09-15 | live]`.
A human's credentials authenticate fine and then `403` on most API calls — the
signature of "this is a person's key, not a service account's".

Two practical consequences:

1. **Comment and approve are different roles.** A Jira sync that only comments
   works with Results API; add auto-approval later and it starts returning `403`.
   Say this when designing a sync.
2. **SCA agent-based APIs require a UI user account, not an API service account**
   `[v: 2026-09-15 | docs.veracode.com/r/c_sourceclear_intro]`. This surprises
   people who standardised on service accounts.

Full mapping: `docs.veracode.com/r/c_API_roles`.

---

## Rate limits `[v: 2026-09-15 | docs.veracode.com/r/About_API_Rate_Limiting]`

| Surface | Limit |
|---|---|
| REST APIs | **500 calls/minute per IP address** |
| XML APIs (general) | 250 calls/minute |
| Flaw Report and Results XML APIs (`detailedreport.do` and friends) | 80 calls/minute |

Exceeding returns `429`; a response header gives the seconds to wait. For XML
loops, pace proactively (0.8–1 s between detailed reports) rather than relying
on `429`.

**Per IP, not per credential** — a shared NAT egress or a busy CI fleet consumes
one shared budget. A portfolio loop that works for one team can fail for another
on the same runner pool. Mention this when writing anything that fans out across
applications.

Minimum viable handling:

```python
def get(self, url, params=None, _retried=False):
    r = self.s.get(url, params=params, timeout=60)
    if r.status_code == 401 and not _retried:
        self._auth()
        return self.get(url, params, _retried=True)
    if r.status_code == 429:
        time.sleep(int(r.headers.get("Retry-After", 30)))
        return self.get(url, params, _retried=_retried)
    r.raise_for_status()
    return r.json()
```

Prefer fewer, larger pages (`size=500` on Applications) over many small ones.

---

## Network

REST (`api.veracode.*`) and XML (`analysiscenter.veracode.*`) are different
hosts. An egress allowlist — a corporate proxy, a sandboxed runner, an AI
workspace — often permits one and not the other. A connection failure on XML
while REST works is network, not auth.

Self-hosted CI runners and on-prem tooling need Veracode's IP ranges allowlisted
`[v: 2026-09-15 | docs.veracode.com/r/c_about_github]`. Symptom is a connection
timeout during upload that looks like a Veracode outage. The current IP list is
published by Veracode — **do not recite ranges from memory.**
