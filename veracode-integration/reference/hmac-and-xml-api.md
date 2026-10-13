# HMAC signing and the legacy XML APIs

**Traps in this file:** an OAuth `client_secret` is not an HMAC key and fails
with a "not hexadecimal" error · the signing library echoes the secret in its
exception messages · `veracode-api-py`'s XML calls ignore the region · XML errors
arrive with HTTP 200 · `<flaw>` analysis type exists only in the ancestry · SCA in
a detailed report is two levels deep · a build's SCA results keep growing after
the scan · a wrong attribute name gives an empty column, not an error.

**Contents:** 1 When HMAC is required · 2 Credentials and regions · 3 Signing with
Veracode's library · 4 Signing without it (Postman, other languages) · 5 XML
endpoint map · 6 Picking a build by scan name · 7 Parsing `detailedreport.do` ·
8 What the data means · 9 Pacing and coverage

---

## 1. When HMAC is required

| Caller or task | Scheme |
|---|---|
| Any `analysiscenter.veracode.*` XML call (`*.do`) | **HMAC only** — OAuth is rejected |
| Findings for a specific build or scan name, per-scan diffs | HMAC (it is XML) |
| Upload & Scan (`uploadfile.do`, `beginprescan.do`, `beginscan.do`) | HMAC |
| Sandbox results as a PDF (`detailedreportpdf.do`, `summaryreportpdf.do`) | HMAC |
| `veracode-api-py`, the Java wrapper, every CI plugin's `vid`/`vkey`, the Pipeline Scan JAR | HMAC |
| REST under `api.veracode.*` | Either. HMAC still works; OAuth is the default for new scripts |
| Power Query (Power BI) | **Neither works for XML.** M has no HMAC-SHA256, so XML is unreachable from Power Query. See `power-bi-and-fabric.md` |

## 2. Credentials and regions

### Two credential pairs, one account

| | HMAC API credentials | OAuth client credentials |
|---|---|---|
| Names | API ID + API key (`vid`/`vkey` in plugins) | `client_id` + `client_secret` |
| Format | Hex. Key ID ≥ 32 chars, key ≥ 128 chars, optional region prefix | Not hex |
| Env vars (convention) | `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET` | `VERACODE_CLIENT_ID` / `VERACODE_CLIENT_SECRET` |
| Created by | `POST /api/authn/v2/api_credentials[/user_id/{id}]` | `POST /api/authn/v2/oauth2/client_credentials` (caller only) |

The same service account can hold both. Putting the OAuth secret into an HMAC
signer fails with `does not seem to be hexadecimal` (library validation) or
`Non-hexadecimal digit found` (raw codec) `[v: 2026-10-02 | live]`. When you see
either, the fix is the other credential pair, not a code change.

### Lifecycle `[v: 2026-10-09 | docs.veracode.com/r/HMAC_credentials]`

- **One active HMAC pair per user.** Generating a new pair revokes the previous one
  **24 hours later** — that window is the rotation grace period.
- Pairs expire after **one year** (the organization's maximum TTL; changing it
  needs Veracode Support).
- **Human users cannot hold API roles** — assigning one returns
  `400 "Cannot assign API roles to human user"` `[v: 2026-09-15 | live]`. A
  human's HMAC keys authenticate, then most calls `403`. Automation belongs on an
  **API service account**. See `identity.md` for creating keys for one without
  logging in as it.

### Region from the key prefix `[v: 2026-10-09 | veracode-api-signing 26.5.0 source]`

A region-scoped credential looks like `vera01ei-<hex>`: an **8-character** prefix,
a hyphen, then the hex value. The **7th character** (index 6) names the region:
`e` → EU, `f` → FedRAMP, `g` → global. No prefix → global. A prefix that is not 8
characters raises `starts with an invalid prefix`.

The library strips the prefix before signing (from both the ID and the secret).
It reports the region name but **does not choose the host for you** — map it:

| Region | REST host | XML base |
|---|---|---|
| global (US Commercial) | `api.veracode.com` | `https://analysiscenter.veracode.com/api` |
| EU | `api.veracode.eu` | `https://analysiscenter.veracode.eu/api` |
| FedRAMP (US Federal) | `api.veracode.us` | `https://analysiscenter.veracode.us/api` |

`[v: 2026-10-09 | docs.veracode.com/r/Region_Domains_for_Veracode_APIs]` —
only the global XML host has been exercised live by this KB.

```python
from veracode_api_signing.regions import get_region_for_api_credential

XML_BASE = {"global": "https://analysiscenter.veracode.com/api",
            "eu":     "https://analysiscenter.veracode.eu/api",
            "fedramp": "https://analysiscenter.veracode.us/api"}

def xml_base():
    # Env var override first; otherwise derive from the HMAC key-id prefix.
    if os.getenv("VERACODE_XML_BASE"):
        return os.environ["VERACODE_XML_BASE"]
    return XML_BASE[get_region_for_api_credential(os.environ["VERACODE_API_KEY_ID"])]
```

## 3. Signing with Veracode's library

**Use `veracode-api-signing` (PyPI, Veracode's own, MIT). Do not hand-roll the
signature in Python.** `[v: 2026-10-09 | 26.5.0]`

```bash
pip install requests veracode-api-signing
```

### With `requests`

```python
import requests
from veracode_api_signing.plugin_requests import RequestsAuthPluginVeracodeHMAC

s = requests.Session()
s.auth = RequestsAuthPluginVeracodeHMAC()     # signs every request on the session
r = s.get(f"{xml_base()}/5.0/getsandboxlist.do", params={"app_id": 12345}, timeout=120)
```

Credentials come from, in order: `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET`,
then `~/.veracode/credentials` using the profile named by `VERACODE_API_PROFILE`
(default `default`):

```ini
[default]
veracode_api_key_id = <id>
veracode_api_key_secret = <secret>
```

Or pass them explicitly: `RequestsAuthPluginVeracodeHMAC(api_key_id=..., api_key_secret=...)`.
Each request gets a fresh signature (timestamp + nonce), so the session can be reused.

### With any other HTTP client (urllib, httpx, aiohttp)

```python
from urllib.parse import urlsplit
from veracode_api_signing.veracode_hmac_auth import generate_veracode_hmac_header

def hmac_header(url, method="GET"):
    u = urlsplit(url)
    path = u.path + (f"?{u.query}" if u.query else "")   # the query string IS signed
    return generate_veracode_hmac_header(u.hostname, path, method,
                                         os.environ["VERACODE_API_KEY_ID"],
                                         os.environ["VERACODE_API_KEY_SECRET"])
```

Build the final URL (query string included, already encoded) **before** signing,
and send exactly that URL. Any re-encoding by the client after signing gives a
`401` with no explanation.

### From a shell

The package installs `veracode_hmac_auth`, which prints a header value:

```bash
curl -sS --compressed -H "Authorization: $(veracode_hmac_auth GET "$URL")" "$URL"
```

The httpie plugin is `http --auth-type=veracode_hmac GET "$URL"` — Veracode's own
doc examples are written that way.

### Never print the exception

`VeracodeCredentialsError` messages include the secret itself (for example
`API secret key <secret> is 40 characters, which is not long enough`). Catch the
library's base exception and replace the message:

```python
from veracode_api_signing.exceptions import VeracodeAPISigningException

try:
    r = s.get(url, params=params, timeout=120)
except (VeracodeAPISigningException, ValueError):
    # Do NOT print the exception: its text can contain the secret.
    sys.exit("HMAC signing failed: VERACODE_API_KEY_ID/_SECRET missing, malformed, "
             "or the OAuth client secret was used (it is not hex and will not sign).")
```

### `veracode-api-py` and XML `[v: 2026-10-09 | 0.9.68 source]`

The wrapper exposes `get_app_list`, `get_sandbox_list`, `get_build_list`,
`get_detailed_report` and friends. Two things to know:

- They return **raw XML bytes**. You still parse, and every guard in §7 applies.
- Its `XMLAPI` class hardcodes `https://analysiscenter.veracode.com/api`, so XML
  calls go to the US Commercial host **whatever the credential's region**. EU and
  FedRAMP users should sign their own requests against the regional host (§2).
  Its REST calls do follow the region.

## 4. Signing without the library

Only when the runtime cannot install it: Postman, Node, Go, PowerShell. Port the
library's `veracode_hmac_auth.py` rather than writing from memory. The algorithm:

```
signing_data = "id={key_id}&host={host}&url={path_with_query}&method={METHOD}"
               key_id and host lower-cased, METHOD upper-cased, path verbatim
k_nonce = HMAC_SHA256(key = bytes.fromhex(secret), msg = nonce_bytes)   # 16 random bytes
k_date  = HMAC_SHA256(key = k_nonce, msg = str(timestamp_ms))
k_sig   = HMAC_SHA256(key = k_date,  msg = "vcode_request_version_1")
sig     = HEX(HMAC_SHA256(key = k_sig, msg = signing_data))
header  = "VERACODE-HMAC-SHA-256 id={key_id},ts={timestamp_ms},nonce={HEX(nonce)},sig={sig}"
```

The two details that turn a hand-rolled signer into an unexplained `401`
`[v: 2026-10-02 | verified against the library]`:

1. The constant is **`vcode_request_version_1`** — not `vcode_request_version_v1`.
2. A region prefix is stripped from **both** the ID and the secret, and the
   stripped ID goes in **both** the signing data and the header.

Also: the clock matters. The timestamp is in the signature, so a runner with a
badly drifted clock fails.

### Postman pre-request script

Tested with Newman against signatures produced by `veracode-api-signing`
`[v: 2026-10-02]`. Set `api_id` / `api_key` as environment variables.

```javascript
const CryptoJS = require('crypto-js');
const url = require('url');
const strip = s => String(s).trim().split('-').pop();          // drop region prefix

const id  = strip(pm.environment.get('api_id'));
const key = strip(pm.environment.get('api_key'));
const u   = url.parse(pm.variables.replaceIn(pm.request.url.toString()));
const data = 'id=' + id.toLowerCase() + '&host=' + String(u.hostname).toLowerCase() +
             '&url=' + String(u.path || '/').replace(/ /g, '%20') +
             '&method=' + pm.request.method.toUpperCase();
const ts = Date.now().toString();
const nonce = CryptoJS.lib.WordArray.random(16);
const kNonce = CryptoJS.HmacSHA256(nonce, CryptoJS.enc.Hex.parse(key));
const kDate  = CryptoJS.HmacSHA256(ts, kNonce);
const kSig   = CryptoJS.HmacSHA256('vcode_request_version_1', kDate);
const sig    = CryptoJS.HmacSHA256(data, kSig).toString(CryptoJS.enc.Hex);
pm.request.headers.upsert({ key: 'Authorization', value:
  'VERACODE-HMAC-SHA-256 id=' + id + ',ts=' + ts + ',nonce=' +
  nonce.toString(CryptoJS.enc.Hex) + ',sig=' + sig });
```

Put it at **collection** level so every request is signed. URL-encode any
free-text query value (an `@` in an email must be `%40`) **before** this script
runs, or the signed URL and the sent URL differ.

## 5. XML endpoint map

Host per §2. Paths follow Veracode's docs `[v: 2026-10-09 | docs.veracode.com
r_getapplist, r_getbuildlist]` where checked; `veracode-api-py` 0.9.68 calls
`/4.0/` for `getapplist.do` and `getbuildlist.do`, and both versions are served.
All are `GET` with query parameters unless noted.

| Call | Path | Key params | Returns |
|---|---|---|---|
| App list | `/5.0/getapplist.do` | optional `include_user_info` | `<app app_id= app_name= …>` |
| App info | `/5.0/getappinfo.do` | `app_id` | profile detail |
| Sandbox list | `/5.0/getsandboxlist.do` | `app_id` | `<sandbox sandbox_id= sandbox_name= …>` |
| Build list | `/5.0/getbuildlist.do` | `app_id`, optional `sandbox_id` (omit = policy builds) | `<build build_id= version= …>` — `version` is the **scan name** |
| Build info | `/5.0/getbuildinfo.do` | `app_id`, `build_id`, `sandbox_id` | build status |
| Apps changed since | `/4.0/getappbuilds.do` | `report_changed_since=MM/DD/YYYY`, `only_latest=false` | apps whose results changed — one call for the whole portfolio |
| Detailed report | `/5.0/detailedreport.do` | `build_id` | every flaw + SCA result for **exactly that build** |
| Detailed report PDF | `/4.0/detailedreportpdf.do` | `build_id` | standard Detailed Report PDF |
| Summary report PDF | `summaryreportpdf.do` | `build_id` | path version *unverified* |
| Upload & Scan | `/5.0/uploadfile.do` (POST), `/5.0/beginprescan.do` (POST), `/5.0/beginscan.do` (POST) | `app_id`, `sandbox_id` … | scan lifecycle; prefer the Java wrapper or a CI plugin |

`getappbuilds.do`'s attribute names and the `report_changed_since` format come
from the docs and have **not** been seen live — print the first response.

**IDs are numeric and XML-only.** `app_id` / `sandbox_id` / `build_id` are not
the REST GUIDs. REST applications carry a numeric `id` and the Applications API
accepts a `legacy_id` filter, but that the two match is **unverified** — prefer
staying in XML end to end for build-scoped work.

**Responses are gzip-compressed XML.** `requests` decompresses automatically;
`curl` needs `--compressed`.

## 6. Picking a build by scan name

Sandboxes commonly hold branch scans and release scans interleaved, with no
ordering guarantee. "The newest release scan" is therefore **not** "the newest
build": reach past newer non-matching builds.

```python
import re

def newest_matching_build(builds, pattern=r"release"):
    """builds: [(build_id:int, version:str)]. Build ids are allocated in ascending
    order, so the highest matching id is the newest matching scan."""
    rx = re.compile(pattern, re.I)
    matching = [(b, v) for b, v in builds if rx.search(v or "")]
    return max(matching, default=None)      # None -> record NO_SCAN_NAME_MATCHED
```

`[v: 2026-10-02 | live]` — selected the older `… Release 2.4` build past a newer
`… Static` branch scan, and the newest of two matching builds when two existed.

- **`<build>` carried no date for sandbox builds** — only `build_id` and
  `version` `[v: 2026-10-02 | live]`. Policy builds may carry
  `policy_updated_date` (docs), but that is when policy was last evaluated, not
  when the scan ran. Order by `build_id` either way, and take the scan date from
  the detailed report afterwards (§7).
- Veracode's auto-generated scan names embed the date
  (`24 Sep 2026 Static - Release 1.2`), which helps humans but is not a sort key.
- Record **every** `version` seen per sandbox in the audit output, so "nothing
  matched" can be checked rather than trusted.

## 7. Parsing `detailedreport.do`

```
<detailedreport ...>                                   root: last_update_time, ...
  <static-analysis published_date= ...>                also <dynamic-analysis>, <manual-analysis>
    <severity level="5">
      <category categoryname= categoryid= >
        <cwe cweid= cwename= >
          <staticflaws>
            <flaw issueid= severity= cweid= categoryname= sourcefile= sourcefilepath=
                  line= module= remediation_status= mitigation_status=
                  affects_policy_compliance= date_first_occurrence=
                  exploit_level= remediation_effort= ... />
  <software_composition_analysis>
    <vulnerable_components>
      <component ...>                                  INVENTORY (one per library)
        <vulnerabilities>
          <vulnerability ... />                        FINDINGS (one per CVE)
```

### The guards — each one is a silent wrong answer when missing

1. **Namespace-agnostic.** Match on the local tag name; the namespace URI has
   changed across versions. `el.tag.rsplit("}", 1)[-1]`, or `find(".//{*}flaw")`.
2. **Keep the ancestry for `<flaw>`.** The analysis type (static, dynamic,
   manual) exists **only** in the ancestor element. A flat `iter("flaw")` merges
   SAST, DAST and manual flaws into one table. Severity, CWE and category appear on
   the flaw *and* its ancestors, and not every flaw carries all three — read the
   attribute, fall back to the ancestor.
3. **SCA is two levels.** `<component>` is inventory; its `<vulnerability>`
   children are the findings. Parsing only components gives a severity-less list
   that looks like data `[v: 2026-10-02 | live — 121 component rows, 0 severities;
   the 237 CVEs were one level down]`.
4. **In-band errors.** XML APIs report errors as an `<error>` root with **HTTP
   200**. Check the root tag before treating a response as "no builds" or "no
   flaws".
5. **Unfinished builds** return a report with no results, not an error. Zero
   flaws *and* zero components → record "results not ready", distinct from "clean".
6. **Every attribute name through a candidate list.** Veracode does not publish
   these schemas. A wrong name yields an **empty column**, not an exception. Keep
   the raw attribute dict alongside the mapped columns, and offer a `--probe` mode
   that prints real attribute names for `<app>`, `<sandbox>`, `<build>`, `<flaw>`,
   `<component>` and one `<component>` subtree before trusting a run.

```python
def tag(el):
    return el.tag.rsplit("}", 1)[-1]

def walk_flaws(el, ctx=None, analysis=None):
    """Yield flaw dicts with inherited severity/CWE/category and the analysis type."""
    t = tag(el)
    if t in ("static-analysis", "dynamic-analysis", "manual-analysis"):
        analysis = t.split("-")[0].upper()
    if t in ("severity", "category", "cwe"):
        ctx = {**(ctx or {}), **el.attrib}            # ancestor values, overridden below
        if t == "severity":
            ctx["severity"] = el.get("level")         # the ancestor names it level=
    if t == "flaw":
        yield {**(ctx or {}), **{k: v for k, v in el.attrib.items() if v},
               "analysis_type": analysis or "UNKNOWN"}
    for child in el:
        yield from walk_flaws(child, ctx, analysis)

def sca_rows(root):
    for comp in root.iter():
        if tag(comp) != "component":
            continue
        vulns = [v for v in comp.iter() if tag(v) == "vulnerability"]
        expected = int(comp.get("vulnerabilities") or 0)  # a COUNT attribute, not a child
        if expected != len(vulns):
            print(f"WARN {comp.get('file_name')}: expected {expected} CVEs, parsed {len(vulns)}")
        for v in vulns:
            yield {**{f"component_{k}": val for k, val in comp.attrib.items()}, **v.attrib}
```

### Attribute sets seen live `[v: 2026-10-02 | live]`

`<component>`: `added_date`, `component_affects_policy_compliance`,
`component_id`, `description`, `file_name`, `library`, `library_id`,
`max_cvss_score`, `sha1`, `vendor`, `version`, `vulnerabilities` (a count).
There is **no** severity attribute on a component.

`<vulnerability>` — the complete set, nine attributes: `cve_id`, `cwe_id`,
`cve_summary`, `cvss_score`, `severity`, `severity_desc`, `first_found_date`,
`mitigation`, `vulnerability_affects_policy_compliance`.

### Dates

- The scan's own date is `static-analysis@published_date`. The root's
  `last_update_time` is when results were last touched — check the analysis
  element **first** or the worse value shadows the better one.
- Emitted shapes include `2026-09-24 12:46:07 UTC` (a trailing zone **name**),
  `+0000` and `Z`. A parser that only handles offsets returns `None` for every
  date, silently disabling date ordering and date checks.

```python
def parse_veracode_date(s):
    s = (s or "").strip().replace(" UTC", "+0000").replace("Z", "+0000")
    for fmt in ("%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None
```

## 8. What the data means

### SAST

- `remediation_status` is real. A build report **includes** flaws `Fixed`
  relative to earlier builds in the same sandbox. Keep them, flagged, and offer an
  open-only filter.
- `Mitigated` still counts as **open** — it is an accepted finding, not a fixed one.
- `Fixed` / `Cannot Reproduce` = closed.

### SCA

- **No open/closed status exists** on `<vulnerability>`. A build report lists what
  was present in that build. Do not invent an `is_open` column — 237 rows of
  "unknown" reads as missing data.
- `mitigation` is a `true`/`false` flag, not a status.
- `severity_desc` is Veracode's own label and is authoritative. A CVSS band
  derived locally (≥9 Very High, ≥7 High, ≥4 Medium, >0 Low, 0 Informational)
  agreed on 237/237 rows `[v: 2026-10-02 | live]`.
- `cwe_id` is absent on some CVEs — Veracode does not assign one to every CVE.
- `first_found_date` = when Veracode first saw that CVE **in this application**.
  It is **not** the CVE publication date, and there is **no** publication date in
  this report. For CVE age, use the agent-based SCA API (`/srcclr/v3`) or NVD.

### A build's SCA results grow after the scan

Veracode re-matches newly published CVEs against the component inventory of
earlier scans **without a rescan**. Observed: 7 of 237 CVEs had a
`first_found_date` up to 8 days **after** the build was scanned, including a
CVSS 9.8 `[v: 2026-10-02 | live]`. So:

- Re-running against the same `build_id` can legitimately return more CVEs.
- SAST flaw sets for a build do not change this way.
- Export a `found_after_scan` flag so reports can separate **known at release**
  from **discovered since**. A 9.8 that appeared four days after release must not
  read as "we shipped knowing this".
- **Give the comparison a tolerance.** Most CVEs carry a `first_found_date` a few
  minutes *after* the scan's `published_date`, because results are processed after
  the scan timestamp. A plain `first_found_date > scan_date` flags nearly every
  row. Parse both dates (§7) and flag only when the gap exceeds a day.

### "Was it fixed after release?"

Not answerable from one build's report, for SAST or SCA. It needs a diff against
the sandbox's newest build. Per-scan diffs (consecutive detailed reports for the
same app) are the pattern — see `recipes.md` §8.

## 9. Pacing and coverage

- XML general: **250/min**. `detailedreport.do` (Flaw Report / Results): **80/min**.
  Space detailed-report calls **0.8–1 s apart**, single-threaded. ~200 apps ≈ 3–4
  minutes. Limits are **per IP**, shared with CI runners on the same egress.
- Typical cost of a build-scoped portfolio extract: 1 app list + 1 sandbox list
  per app + 1 build list per sandbox + 1 detailed report per selected build.
- Write an **audit row for every app and every sandbox** with an outcome:
  `MATCHED_AND_EXPORTED`, `MATCHED_BUT_REPORT_EMPTY`, `NO_SCAN_NAME_MATCHED`,
  `NO_BUILDS_IN_SANDBOX`, `APP_HAS_NO_SANDBOXES`, `ERROR`. Include every scan name
  seen and which candidate builds were passed over.
- Offer `--save-xml DIR` to keep raw responses, so a disputed column can be
  checked against the source without re-pulling.
- When several sandboxes scan the same artifact, their rows are identical sets —
  count on the composite key (SKILL.md invariant 12), and default reports to
  slicing by sandbox so the grain is visible.
