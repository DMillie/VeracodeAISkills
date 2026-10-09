# Policy and compliance

**Traps in this file:** `violates_policy=TRUE` on the Findings API gives you
*flaws*, not a pass/fail verdict — the verdict is on the application object ·
the verdict enum is `SCREAMING_SNAKE_CASE` · `/policies` returns
`_embedded.policy_versions` · policy attachment mechanics are unverified ·
Pipeline Scan policy evaluation is local and does not update the profile.

---

## "Did this application pass policy?"

The most common AppSec question, and the Findings API does not answer it.

### The verdict is on the application `[v: 2026-09-18 | live]`

`GET /appsec/v1/applications` already carries each application's verdict, so a
portfolio compliance view is **one paginated call**, no per-application requests:

```jsonc
{
  "guid": "…",
  "last_policy_compliance_check_date": "…",
  "profile": {
    "name": "…",
    "policies": [ { "name": "…", "policy_compliance_status": "DID_NOT_PASS" } ]
  }
}
```

The field was read live; its `profile` parent is from the published schema, so
print one application on the first run before indexing.

**The enum is `SCREAMING_SNAKE_CASE`.** `DID_NOT_PASS` was seen live; the others
(`PASSED`, `CONDITIONAL_PASS`, `NOT_ASSESSED`, …) follow the same shape but have
not all been observed. Compare against the enum, or normalise underscores to
spaces first — `"DID NOT PASS" in status` silently never matches.

Filter server-side with `policy_compliance=DID_NOT_PASS`, and find recently
evaluated apps with `policy_compliance_checked_after`
(`yyyy-mm-ddThh:mm:ss.000Z`).

What you can build from this call alone: compliance rate; verdict breakdown;
apps failing; apps never assessed; scan coverage and recency; slicing by business
unit, criticality, team and policy; verdict freshness.

### Summary Report — detail, not the verdict

`GET /appsec/v2/applications/{application_guid}/summary_report`
`[v: 2026-09-15 | docs.veracode.com/r/c_sum_report_gen_rest]`

| Param | Notes |
|---|---|
| `context` | Sandbox GUID, for a sandbox-scoped summary. Omit for Policy scope. |

Returns severity counts and scan metadata for the profile. **Response field
names are unverified** — none of this KB's live runs have captured one. A wrong
field name yields `null`, not an error: every tile blanks and compliance reads
0%. Inspect the first response and pin the fields. It is also one call per app,
so do not use it for the verdict when the applications list already has it.

### Related and distinct

- `violates_policy=TRUE` on Findings → the individual flaws that breach policy.
- `include_exp_date=TRUE` → `grace_period_expires_date`, i.e. which flaws are
  inside a grace period and when that runs out. This is what "we're passing today
  but fail in 12 days" looks like.

For a compliance dashboard you usually want all three: the verdict from the
applications list, the offending flaws from Findings, and the grace-period clock.

---

## Policy API `[v: 2026-09-15 | docs.veracode.com/r/c_policy_rest_api, /r/Creating_a_Policy_with_the_REST_API]`

Base path: `/appsec/v1/policies`

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/appsec/v1/policies` | Create |
| `GET` | `/appsec/v1/policies` | List |
| `GET` | `/appsec/v1/policies/{guid}` | Read |
| `PUT` | `/appsec/v1/policies/{guid}` | Update |
| `DELETE` | `/appsec/v1/policies/{guid}` | Delete |

The list returns **`_embedded.policy_versions`**, not `_embedded.policies`
`[v: 2026-09-15 | live]`. Reading the obvious key returns nothing, without error.

Individual method paths beyond `POST` are inferred from convention and are
**unverified** — confirm against
`app.swaggerhub.com/apis/Veracode/veracode-policy_api_specification/1.0`.

The API can also **evaluate** an application or sandbox against a policy,
returning why it passes or fails, including scan-frequency requirements and flaws
past their grace-period due date. The evaluation endpoint path is **unverified**.

### Create body `[v: 2026-09-15 | docs.veracode.com/r/Creating_a_Policy_with_the_REST_API]`

```jsonc
{
  "name": "TestPolicy",
  "type": "BLACKLIST",
  "description": "Policy to test create endpoint",
  "vendor_policy": false,
  "finding_rules": [
    {
      "type": "MAX_SEVERITY",
      "scan_type": ["DYNAMIC", "MANUAL", "STATIC"],
      "value": "3"
    }
  ],
  "scan_type": ["SCA"],
  "value": "14212"
}
```

`finding_rules[].type` values beyond `MAX_SEVERITY` (CWE rules, category rules,
CVSS rules), scan-frequency rule schema, and grace-period fields are documented
by Veracode under "Policy API Rules Properties" but are **not captured here.**
Point the user there rather than inventing rule types.

Note `value` is a **string** even for numeric severity.

**Role required:** Policy Administrator.

### Attaching a policy to an application

The mechanism is **unverified** in this KB — likely via the application profile's
policy field on the Applications API. Do not guess the field name; check the
Applications spec.

### Policy as code

`github.com/tjarrettveracode/veracode-policy-examples` holds example policies as
JSON that can be POSTed into an organization. Community-maintained, not official
Veracode support — say so if you recommend it.

---

## Where policy is evaluated — three different places

This confuses people constantly.

| Where | What it means | Reaches the profile? |
|---|---|---|
| **Policy scan** (Upload & Scan) | Authoritative compliance verdict on the application profile | Yes |
| **Sandbox scan** | Evaluated against the same policy for developer feedback | No — sandboxes do not change compliance |
| **Pipeline Scan** | Local pass/fail using `veracode_policy_name` or a downloaded `policy_file`, decided inside the CI run | **No** |

So a team whose PR gate is green can still be failing policy, and a team that
fixed everything in a sandbox has not changed their compliance status. If a user
conflates these, correct it explicitly — it is usually the root cause of a
"the API is wrong" report.

## Grace periods

Policies can allow a grace period before a flaw causes failure. Surface it with
`include_exp_date=TRUE` on Findings and read `grace_period_expires_date`. A
compliance report that ignores grace periods will disagree with the Veracode UI
and the user will assume your script is broken.
