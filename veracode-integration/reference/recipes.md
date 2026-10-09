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


def first_run_start():
    """The server rejects any start date older than six months BEFORE TODAY:
    400 [last_updated_start_date must be (0-6 months) before today's date]
    So there is no backfill past that; history accrues from the first run."""
    return datetime.now(timezone.utc) - timedelta(days=180)
```

Persist the last successful `last_updated_start_date` and resume from it, with a
few minutes of overlap rather than risking a gap. Tell the user up front that the
first run reaches back six months at most.

---

## 4. Compliance check — "are we passing?"

The verdict is on the application object, so the whole portfolio is one
paginated call `[v: 2026-09-18 | live]`:

```python
def portfolio_compliance(vc):
    rows = []
    for a in vc.paged(f"{vc.base}/appsec/v1/applications", "applications", {"size": 500}):
        prof = a.get("profile", {})                 # print one app on first run: confirm the parent
        pol = (prof.get("policies") or [{}])[0]
        status = pol.get("policy_compliance_status")  # SCREAMING_SNAKE: DID_NOT_PASS, ...
        rows.append({"app": prof.get("name"), "policy": pol.get("name"),
                     "status": status or "NOT_ASSESSED",
                     "checked": a.get("last_policy_compliance_check_date")})
    return rows


def breaching_findings(vc, app_name):
    """The offending flaws for one app, plus the grace-period clock."""
    app = vc.app_guid(app_name)
    return [f for f in vc.paged(
                f"{vc.base}/appsec/v2/applications/{app}/findings", "findings",
                {"violates_policy": "TRUE", "include_exp_date": "TRUE"})
            if f["finding_status"]["status"] == "OPEN"]
```

Compare `status` to the enum, never `"DID NOT PASS" in status` — the underscores
make that silently false.

Reminder for the user: a green **Pipeline Scan** does not mean policy compliance,
and fixing a **sandbox** does not change it either. Only a Policy scan does.
See `policy-and-compliance.md`.

---

## 5. CI credential expiry warning

Prevents the "nothing changed and the pipeline broke" incident.

```python
def creds_expiring(vc, user_ids, days=14):
    """Warn before service accounts' HMAC credentials lapse (needs Admin API)."""
    soon = []
    for uid in user_ids:
        c = vc.get(f"{vc.base}/api/authn/v2/api_credentials/user_id/{uid}")
        # `expiration_ts` matches Veracode's examples; print `c` once to confirm.
        exp = datetime.fromisoformat(str(c.get("expiration_ts", "")).replace("Z", "+00:00"))
        left = (exp - datetime.now(timezone.utc)).days
        if left <= days:
            soon.append((uid, c.get("api_id"), left))
    return soon
```

Run it weekly. Rotating is one call — `POST .../api_credentials/user_id/{uid}` —
and the old pair keeps working for 24 hours, which is the window to update the
secret store (`identity.md`).

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

---

## 7. Findings from the newest scan *named* "release" (XML, HMAC)

The request behind this recipe: *"for every application, the results of the most
recent release scan"*, where release and branch scans share sandboxes. REST
cannot answer it (SKILL.md invariant 5). The XML chain can, and this pattern ran
live `[v: 2026-10-02 | live]`: it reached past a newer branch scan to the older
release build, and chose the newest of two matching builds.

Before the code, tell the user:

- It needs the **HMAC** pair, and `analysiscenter.veracode.*` must be reachable.
- A build's SCA results can grow after the scan (`hmac-and-xml-api.md` §8).
- Several sandboxes scanning the same artifact give identical rows — count on the
  composite key.
- If release and branch builds share a sandbox, the sandbox layout is the root
  problem; the REST view of that sandbox flips with every scan.

```python
#!/usr/bin/env python3
"""Findings from each sandbox's newest scan whose NAME matches a pattern (default: release).

REST cannot do this: Findings v2 is context-scoped with no scan/build filter.
XML can: getbuildlist.do lists every build with its scan name (`version`), and
detailedreport.do returns results for exactly one build. XML is HMAC-only.

  pip install requests veracode-api-signing
  env: VERACODE_API_KEY_ID / VERACODE_API_KEY_SECRET  (HMAC pair; role: Results API,
       plus noteamrestrictionapi to see every application)
  python release_scan.py --match release --out-prefix release
"""
import argparse, csv, os, re, sys, time
import xml.etree.ElementTree as ET
import requests
from veracode_api_signing.exceptions import VeracodeAPISigningException
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC
from veracode_api_signing.regions import get_region_for_api_credential

XML_BASE = {"global": "https://analysiscenter.veracode.com/api",
            "eu": "https://analysiscenter.veracode.eu/api",
            "fedramp": "https://analysiscenter.veracode.us/api"}


def tag(el):
    return el.tag.rsplit("}", 1)[-1]          # namespace-agnostic: the URI has changed over time


class Xml:
    def __init__(self, base, report_gap=1.0):
        self.base, self.gap, self.s = base, report_gap, requests.Session()
        self.s.auth = RequestsAuthPluginVeracodeHMAC()
        self.calls = 0

    def __call__(self, call, **params):
        while True:
            try:
                r = self.s.get(f"{self.base}/5.0/{call}.do", params=params, timeout=120)
            except VeracodeAPISigningException:
                # Never print this exception: its message can contain the secret.
                sys.exit("HMAC signing failed: VERACODE_API_KEY_ID/_SECRET missing, malformed, "
                         "or the OAuth client secret was used (not hex; it will not sign).")
            self.calls += 1
            if r.status_code != 429:
                break
            time.sleep(int(r.headers.get("Retry-After", 30)))
        if r.status_code in (401, 403):
            sys.exit(f"{r.status_code} on {call}.do: needs the HMAC pair of an API service "
                     f"account with Results API (403 = missing role, 401 = wrong key/region)")
        r.raise_for_status()
        root = ET.fromstring(r.content)
        if tag(root) == "error":               # XML APIs report errors IN-BAND with HTTP 200
            raise RuntimeError(f"{call}.do: {(root.text or '').strip()}")
        if call == "detailedreport":
            time.sleep(self.gap)               # detailedreport.do is limited to 80/min per IP
        return root


def walk_flaws(el, ctx=None, analysis=None):
    """Flaw attrs, inheriting severity/CWE/category from ancestors; analysis type
    exists ONLY in the ancestry, so a flat iter('flaw') would merge SAST/DAST/manual."""
    t = tag(el)
    if t in ("static-analysis", "dynamic-analysis", "manual-analysis"):
        analysis = t.split("-")[0].upper()
    if t in ("severity", "category", "cwe"):
        ctx = {**(ctx or {}), **el.attrib}
        if t == "severity":                    # ancestor carries it as level=
            ctx["severity"] = el.get("level")
    if t == "flaw":
        yield {**(ctx or {}), **{k: v for k, v in el.attrib.items() if v},
               "analysis_type": analysis or "UNKNOWN"}
    for child in el:
        yield from walk_flaws(child, ctx, analysis)


def sca(root):
    """SCA is TWO levels: <component> = inventory, <vulnerability> children = findings."""
    comps, vulns, expected = [], [], 0
    for c in (e for e in root.iter() if tag(e) == "component"):
        comps.append(dict(c.attrib))
        expected += int(c.get("vulnerabilities") or 0)          # a COUNT attribute
        for v in (e for e in c.iter() if tag(e) == "vulnerability"):
            vulns.append({"component": c.get("file_name") or c.get("library"),
                          "component_version": c.get("version"), **v.attrib})
    return comps, vulns, expected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", default="release", help="regex matched against the scan name")
    ap.add_argument("--app", help="exact application name (default: all)")
    ap.add_argument("--out-prefix", default="release_scan")
    a = ap.parse_args()
    rx = re.compile(a.match, re.I)
    key_id = os.getenv("VERACODE_API_KEY_ID", "")
    base = os.getenv("VERACODE_XML_BASE") or XML_BASE[get_region_for_api_credential(key_id or "x")]
    xml = Xml(base)

    flaws, cves, audit = [], [], []
    apps = [(x.get("app_id"), x.get("app_name")) for x in xml("getapplist").iter() if tag(x) == "app"]
    apps = [p for p in apps if not a.app or p[1] == a.app]
    for app_id, app_name in apps:
        sandboxes = [(s.get("sandbox_id"), s.get("sandbox_name"))
                     for s in xml("getsandboxlist", app_id=app_id).iter() if tag(s) == "sandbox"]
        if not sandboxes:
            audit.append({"app": app_name, "outcome": "APP_HAS_NO_SANDBOXES"})
            continue
        for sb_id, sb_name in sandboxes:
            row = {"app": app_name, "sandbox": sb_name}
            builds = [(int(b.get("build_id")), b.get("version", ""))
                      for b in xml("getbuildlist", app_id=app_id, sandbox_id=sb_id).iter()
                      if tag(b) == "build"]
            matching = [b for b in builds if rx.search(b[1])]
            row.update(builds=len(builds), matching=len(matching),
                       all_scan_names=" | ".join(v for _, v in sorted(builds)))
            if not builds:
                audit.append({**row, "outcome": "NO_BUILDS_IN_SANDBOX"}); continue
            if not matching:
                audit.append({**row, "outcome": "NO_SCAN_NAME_MATCHED"}); continue
            build_id, scan_name = max(matching)     # build ids ascend: highest = newest match
            rep = xml("detailedreport", build_id=build_id)
            sa = next((e for e in rep.iter() if tag(e) == "static-analysis"), None)
            scan_date = (sa.get("published_date") if sa is not None else None) or rep.get("last_update_time")
            ident = {"app": app_name, "sandbox": sb_name, "build_id": build_id,
                     "scan_name": scan_name, "scan_date": scan_date}
            f = [{**ident, **x} for x in walk_flaws(rep)]
            comps, v, expected = sca(rep)
            v = [{**ident, **x} for x in v]
            flaws += f; cves += v
            outcome = "MATCHED_AND_EXPORTED" if (f or comps) else "MATCHED_BUT_REPORT_EMPTY"
            note = "" if expected == len(v) else f"SCA MISMATCH expected {expected} parsed {len(v)}"
            audit.append({**row, "selected_build_id": build_id, "selected_scan_name": scan_name,
                          "flaws": len(f), "components": len(comps), "cves": len(v),
                          "outcome": outcome, "notes": note})

    for name, rows in (("flaws", flaws), ("sca_cves", cves), ("audit", audit)):
        cols = list(dict.fromkeys(k for r in rows for k in r))
        with open(f"{a.out_prefix}_{name}.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=cols or ["empty"])
            w.writeheader(); w.writerows(rows)
    print(f"{len(apps)} apps, {xml.calls} XML calls: {len(flaws)} flaws, {len(cves)} CVEs. "
          f"Read {a.out_prefix}_audit.csv before trusting an empty result.")


if __name__ == "__main__":
    main()
```

Extend it the same way the live version was extended: a `--probe` flag that
prints raw attribute names first, `--save-xml DIR`, `--open-only`, a
components (inventory) table, a `found_after_scan` column on CVE rows
(`first_found_date` later than `scan_date`), and the per-app candidate list in
the audit (`matching_builds_detail`).

---

## 8. Per-scan diff — "what closed and reopened in each scan"

Example ask: *in the last month's policy scans, how many findings of a CWE closed
in a file and came back as new issue ids in the same scan — and how many accepted
mitigations did that wipe?* REST cannot say "closed in scan X" (current state
only, no closed date). Diff **consecutive** detailed reports instead.

```
getappbuilds.do (4.0)  report_changed_since=MM/DD/YYYY, only_latest=false
                       -> apps with changed results in the window       (1 call)
getbuildlist.do        app_id=   (no sandbox_id = policy builds)  -> build_id, version
detailedreport.do      newest first, until the first scan published BEFORE the
                       window (the baseline); cap ~25 per app; 0.8 s apart
```

```python
def is_closed(f):
    return f.get("remediation_status", "").lower() in ("fixed", "cannot reproduce")

def diff(prev, cur):
    """prev/cur: {issueid: flaw} from two consecutive STATIC reports of one app."""
    closed = [i for i, f in prev.items() if not is_closed(f) and (i not in cur or is_closed(cur[i]))]
    opened = [i for i, f in cur.items() if i not in prev and not is_closed(f)]
    return closed, opened
```

Group `closed` and `opened` by `(sourcefilepath/sourcefile, cweid)`; a row where
both are non-zero is churn. `mit_wiped` = closed flaws whose
`mitigation_status` contains `accepted`.

Guards that matter here: skip reports with no `<static-analysis>` (DAST-only
builds) and in-band `<error>` (in-progress builds) rather than reading them as
"everything closed"; walk only the static subtree; diff consecutive reports
instead of trusting `remediation_status=New/Fixed`, so a flaw fixed three scans
ago is not recounted.

Limits to state: rough by design — an unrelated fix and an unrelated new flaw of
the same CWE in the same file count as churn, so matching counts (9 closed / 9
opened) are the strong signal. Policy scans only; an app's first scan has no
baseline. `getappbuilds.do` attribute names and accepted-mitigation
`mitigation_status` values have not been seen live — validate on a tenant with
known mitigations before quoting the wiped count.
