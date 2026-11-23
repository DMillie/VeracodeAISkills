# Evidence register: API

| ID | Basis | Checked | Source or observation | Claim as written in the skill | File |
|---|---|---|---|---|---|
| API-01 | lab | 2026-11-11 | observed in the lab | `GET /appsec/v1/applications?name=X` is a partial, case-insensitive match; re-filter for the exact `profile.name`. Empty collections omit `_embedded`. Paginate (`page`, `size`, `page.total_pages`). | `shared/reference/facts/rest-api.md` |
| API-02 | lab | 2026-11-11 | observed in the lab | Application fields: `guid` (REST), `id` (legacy numeric app_id for XML/wrapper), `profile.{name,business_criticality,policies[].policy_compliance_status,teams[],git_repo_url,...}`. `policy_compliance_status` is SCREAMING_SNAKE_CASE (`DID_NOT_PASS`). | `shared/reference/facts/rest-api.md` |
| API-03 | lab | 2026-11-11 | see lab run 1 for the exact response | `POST /appsec/v1/applications` with `{"profile": {"name", "business_criticality", ...}}` creates a profile. | `shared/reference/facts/rest-api.md` |
