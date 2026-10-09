# Worked recipes

End-to-end patterns. Each crosses an endpoint boundary — that is where generated
code breaks. Invariants are repeated as inline comments on purpose.

---

## 0. The client every recipe uses

```python
#!/usr/bin/env python3
import base64, os, sys, time
import requests

API_BASE = os.getenv("VERACODE_API_BASE", "https://api.veracode.com")


class Veracode:
    """OAuth 2.0 client with token refresh and 429 backoff."""

    def __init__(self, base=API_BASE):
        self.base, self.s = base, requests.Session()
        self._auth()

    def _auth(self):
        basic = base64.b64encode(
            f"{os.environ['VERACODE_CLIENT_ID']}:"
            f"{os.environ['VERACODE_CLIENT_SECRET']}".encode()).decode()
        r = requests.post(
            f"{self.base}/api/authn/v2/oauth2/token",
            headers={"Authorization": f"Basic {basic}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            data="grant_type=client_credentials", timeout=30)
        r.raise_for_status()
        self.s.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

    def _req(self, method, url, _retried=False, **kw):
        r = self.s.request(method, url, timeout=60, **kw)
        if r.status_code == 401 and not _retried:      # token expired
            self._auth()
            return self._req(method, url, _retried=True, **kw)
        if r.status_code == 429:                        # 500 req/min per IP
            time.sleep(int(r.headers.get("Retry-After", 30)))
            return self._req(method, url, _retried=_retried, **kw)
        if r.status_code == 403:
            raise SystemExit(f"403 on {url} — the service account is missing a "
                             f"role. See auth-and-access.md.")
        r.raise_for_status()
        return r

    def get(self, url, params=None):
        return self._req("GET", url, params=params).json()

    def post(self, url, json=None):
        return self._req("POST", url, json=json)

    def paged(self, url, collection, params=None):
        """Integer pagination. Applies to EVERY collection endpoint."""
        page = 0
        while True:
            body = self.get(url, dict(params or {}, page=page, size=100))
            yield from body.get("_embedded", {}).get(collection, [])
            if page >= body.get("page", {}).get("total_pages", 1) - 1:
                return
            page += 1

    # name -> guid. `name` is a PARTIAL, case-insensitive match.
    def app_guid(self, name):
        apps = list(self.paged(f"{self.base}/appsec/v1/applications",
                               "applications", {"name": name}))
        exact = [a for a in apps if a["profile"]["name"].lower() == name.lower()]
        if len(exact) != 1:
            sys.exit(f"Need exactly 1 app named {name!r}; matched {len(apps)}: "
                     + ", ".join(a["profile"]["name"] for a in apps))
        return exact[0]["guid"]

    def sandbox_guid(self, app_guid, sandbox_name):
        # Paginated — an unpaginated lookup reports a real sandbox as missing.
        sb = next((s for s in self.paged(
            f"{self.base}/appsec/v1/applications/{app_guid}/sandboxes", "sandboxes")
            if s["name"] == sandbox_name), None)
        if not sb:
            sys.exit(f"No sandbox named {sandbox_name!r}")
        return sb["guid"]
```

---

## 1. SAST findings in a named sandbox, High and above

```python
SEV = {5: "Very High", 4: "High", 3: "Medium", 2: "Low", 1: "Very Low", 0: "Info"}


def sandbox_sast(vc, app_name, sandbox_name, min_sev=4):
    app = vc.app_guid(app_name)
    sb = vc.sandbox_guid(app, sandbox_name)

    findings = vc.paged(
        f"{vc.base}/appsec/v2/applications/{app}/findings", "findings",
        {"context": sb,                 # omit for Policy scope
         "scan_type": "STATIC",         # SCA cannot be combined with this
         "severity_gte": min_sev})      # NOT `severity` — that is exact-match

    rows = []
    for f in findings:
        # Closed findings ARE returned by default.
        if f["finding_status"]["status"] != "OPEN":
            continue
        d = f["finding_details"]        # STATIC schema; SCA differs entirely
        rows.append((d["severity"],     # int for STATIC, str for SCA
                     f["issue_id"], d["cwe"]["id"],
                     d["file_path"], d.get("file_line_number", "?")))

    rows.sort(reverse=True)
    print(f"{len(rows)} open SAST findings >= {SEV[min_sev]}\n")
    for sev, iid, cwe, path, line in rows:
        print(f"  [{SEV[sev]:>9}] #{iid:<8} CWE-{cwe:<5} {path}:{line}")
    return rows


if __name__ == "__main__":
    sandbox_sast(Veracode(), "Payment-Gateway", "feature-branch")
```

**Variants:** Policy scope → drop `context`. Policy-violating only → add
`violates_policy=TRUE`. New this scan → `new=true`. Grace-period clock →
`include_exp_date=TRUE`.

**SCA:** separate call with `scan_type=SCA`, and a different field branch:

```python
for f in sca_findings:
    d = f["finding_details"]
    print(d["cve"]["name"], d["component_filename"], d["severity"])  # severity is a STRING
```

---

## 2. Jira sync that does not duplicate

The naive version comments on every finding every run, forever.
`include_annot=TRUE` returns each finding's existing `annotations[]`, which is the
only way to know what you already ticketed — there is no `GET /annotations`.

```python
TICKET_TAG = "veracode-jira-sync"     # machine-readable marker in the comment


def already_ticketed(finding):
    for a in finding.get("annotations", []):
        if a.get("action") == "COMMENT" and TICKET_TAG in (a.get("comment") or ""):
            return True
    return False


def annotate(vc, app_guid, issue_ids, comment, action="COMMENT"):
    # issue_list is a COMMA-SEPARATED STRING, not a JSON array.
    # Max length undocumented — chunk conservatively.
    for i in range(0, len(issue_ids), 50):
        chunk = issue_ids[i:i + 50]
        vc.post(f"{vc.base}/appsec/v2/applications/{app_guid}/annotations",
                json={"issue_list": ",".join(str(x) for x in chunk),
                      "comment": comment, "action": action})


def sync_to_jira(vc, app_name, jira):
    app = vc.app_guid(app_name)

    findings = list(vc.paged(
        f"{vc.base}/appsec/v2/applications/{app}/findings", "findings",
        {"scan_type": "STATIC",
         "severity_gte": 4,
         "violates_policy": "TRUE",
         "include_annot": "TRUE"}))    # <- what makes this idempotent

    todo = [f for f in findings
            if f["finding_status"]["status"] == "OPEN" and not already_ticketed(f)]
    print(f"{len(findings)} findings, {len(todo)} need tickets")

    for f in todo:
        d = f["finding_details"]
        key = jira.create_issue(
            summary=f"CWE-{d['cwe']['id']} in {d['file_path']}",
            description=f.get("description", ""),
            labels=["veracode", f"severity-{d['severity']}"])
        annotate(vc, app, [f["issue_id"]],
                 f"[{TICKET_TAG}] Ticket created: {key}")
        # Key your Jira record on (context_guid, issue_id) — issue_id uniqueness
        # across Policy vs Sandbox scope is NOT documented.
```

**Design notes to raise with the user:**

- `COMMENT` does not change `resolution_status`. To push a Jira resolution back
  into Veracode, post a proposal (`FP`, `APPDESIGN`, `NETENV`, `OSENV`, `LIBRARY`,
  `ACCEPTRISK`), then `ACCEPTED`/`REJECTED` from an account with the Mitigation
  API role. Comment-only needs Results API; approval needs more.
- **Sandbox-scoped annotation is unverified.** Sync Policy scope unless they have
  confirmed the parameter.
- No webhooks. This is a polling job — schedule it, and for a large portfolio
  drive the delta off the Reporting API rather than looping Findings per app.

---

## 3. Nightly portfolio extract for BI

Do **not** loop the Findings API across hundreds of applications — 500 calls/min
per IP and you will be throttled partway, which looks like a permissions failure.

```python
from datetime import datetime, timedelta, timezone


def nightly_findings(vc, since: datetime):
    body = {
        "report_type": "FINDINGS",
        # Format is "YYYY-MM-DD HH:MM:ss" — NOT ISO-8601 with a trailing Z.
        "last_updated_start_date": since.strftime("%Y-%m-%d %H:%M:%S"),
        "policy_sandbox": "Policy",
        "status": "open",
    }
    rid = vc.post(f"{vc.base}/appsec/v1/analytics/report",
                  json=body).json()["id"]

    deadline = time.time() + 900
    while time.time() < deadline:
        resp = vc.get(f"{vc.base}/appsec/v1/analytics/report/{rid}")
        # Status field/values are UNVERIFIED — print `resp` on first run and pin.
        status = str(resp.get("status", "")).upper()
        if status.startswith("COMPLET"):
            return resp
        if status in ("FAILED", "ERROR"):
            raise RuntimeError(resp)
        time.sleep(10)
    raise TimeoutError(rid)


def backfill(vc, start: datetime, end: datetime):
    """Reports cap at SIX MONTHS. Chunk longer ranges."""
    cur = start
    while cur < end:
        stop = min(cur + timedelta(days=180), end)
        yield nightly_findings(vc, cur)          # pass `stop` as end_date in prod
        cur = stop
```

Persist the last successful `last_updated_start_date` and resume from it, with a
few minutes of overlap rather than risking a gap.

---

## 4. Compliance check — "are we passing?"

```python
def compliance(vc, app_name, sandbox=None):
    app = vc.app_guid(app_name)
    params = {"context": vc.sandbox_guid(app, sandbox)} if sandbox else {}

    # The verdict. Response field names are UNVERIFIED — print and pin.
    summary = vc.get(f"{vc.base}/appsec/v2/applications/{app}/summary_report",
                     params=params)

    # The offending flaws, plus the grace-period clock.
    breaching = list(vc.paged(
        f"{vc.base}/appsec/v2/applications/{app}/findings", "findings",
        dict(params, violates_policy="TRUE", include_exp_date="TRUE")))

    open_breaching = [f for f in breaching
                      if f["finding_status"]["status"] == "OPEN"]
    return summary, open_breaching
```

Reminder for the user: a green **Pipeline Scan** does not mean policy compliance,
and fixing a **sandbox** does not change it either. Only a Policy scan does.
See `policy-and-compliance.md`.

---

## 5. CI credential expiry warning

Prevents the "nothing changed and the pipeline broke" incident.

```python
def creds_expiring(vc, days=14):
    """Warn before a service account's API credentials lapse."""
    me = vc.get(f"{vc.base}/api/authn/v2/api_credentials")
    # Field name for the expiry is UNVERIFIED — inspect `me` and pin it.
    print(me)
    return me
```

Run it weekly against each CI service account.

---

## 6. GitHub Action: PR gate + Security tab

Full workflow in `ci-integrations.md`. Shape:

```
checkout → build artifact → Pipeline Scan (fail_build, baseline_file)
        → convert to SARIF (if: always()) → upload-sarif (if: always())
```

with `permissions: security-events: write`.

Raise unprompted, because they surface in week one:

1. **Baseline**, or day one fails on the whole backlog and the gate gets disabled.
2. **Packaging** — a wrongly packaged artifact scans clean and looks like success.
3. **Fork PRs** cannot write to the Security tab with the default token.
4. Compliance reporting is a **separate** Policy scan job on main.
