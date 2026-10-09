# Authentication, roles and rate limits

**Traps in this file:** two live auth schemes that are not interchangeable ·
wrappers and CI plugins are HMAC-only · a `403` is almost always a missing role,
not a bad credential.

---

## Which scheme for which caller

| Caller | Scheme |
|---|---|
| Your own Python/Node/Go REST script | **OAuth 2.0 client credentials** |
| `veracode-api-py`, Java API wrapper, `httpie --auth-type=veracode_hmac` | **HMAC** |
| GitHub Actions / Jenkins / GitLab / Azure DevOps plugins (`vid`/`vkey`) | **HMAC** |
| Pipeline Scan JAR or Docker image | **HMAC** |
| Legacy XML APIs | **HMAC** |

Getting this wrong is the most common `401`. Ask which one they are on before
debugging anything else.

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
- Token lifetime is documented only as "short-lived" — the exact value is
  **unverified**. Do not hardcode an expiry; refresh on `401` and retry once.
- Advantages Veracode cites over HMAC: expiring credentials, narrower permission
  scoping.

## HMAC `[v: 2026-09-15 | docs.veracode.com/r/c_api_credentials3]`

```
Authorization: VERACODE-HMAC-SHA-256 id=...,ts=...,nonce=...,sig=...
```

Do not hand-roll the signature. Use `veracode-api-signing`:

```python
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

r = requests.get(f"{base}/appsec/v1/applications",
                 auth=RequestsAuthPluginVeracodeHMAC(), timeout=60)
```

It reads `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET`, or `~/.veracode/credentials`:

```ini
[default]
veracode_api_key_id = <id>
veracode_api_key_secret = <secret>
```

For `httpie`: `http --auth-type=veracode_hmac GET "<url>"`. Veracode's own doc
examples are written this way — when you copy one, remember the reader may be on
OAuth.

## Environment variables

| Variable | Used by |
|---|---|
| `VERACODE_CLIENT_ID` / `VERACODE_CLIENT_SECRET` | OAuth |
| `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET` | HMAC |
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
| Flaw Report and Results XML APIs | 80 calls/minute |

Exceeding returns `429`; a response header gives the seconds to wait.

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

Self-hosted CI runners and on-prem tooling need Veracode's IP ranges allowlisted
`[v: 2026-09-15 | docs.veracode.com/r/c_about_github]`. Symptom is a connection
timeout during upload that looks like a Veracode outage. The current IP list is
published by Veracode — **do not recite ranges from memory.**
