# Policy and compliance

**Traps in this file:** `violates_policy=TRUE` on the Findings API gives you
*flaws*, not a pass/fail verdict — the verdict comes from the Summary Report ·
policy attachment mechanics are unverified · Pipeline Scan policy evaluation is
local and does not update the profile.

---

## "Did this application pass policy?"

The most common AppSec question, and the Findings API does not answer it.

`GET /appsec/v2/applications/{application_guid}/summary_report`
`[v: 2026-09-15 | docs.veracode.com/r/c_sum_report_gen_rest]`

| Param | Notes |
|---|---|
| `context` | Sandbox GUID, for a sandbox-scoped summary. Omit for Policy scope. |

Returns a summary of results for the application profile: compliance status,
severity counts, scan metadata. **Exact response field names are unverified** —
inspect the first response and pin the field rather than guessing
`policy_compliance_status`.

Related and distinct:

- `violates_policy=TRUE` on Findings → the individual flaws that breach policy.
- `include_exp_date=TRUE` → `grace_period_expires_date`, i.e. which flaws are
  inside a grace period and when that runs out. This is what "we're passing today
  but fail in 12 days" looks like.

For a compliance dashboard you usually want all three: the verdict from the
summary report, the offending flaws from Findings, and the grace-period clock.

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
