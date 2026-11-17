# REST API (application profiles)

- `GET /appsec/v1/applications?name=X` is a partial, case-insensitive match; re-filter for the
  exact `profile.name`. Empty collections omit `_embedded`. Paginate (`page`, `size`,
  `page.total_pages`). **[live 2026-11-11]**
- Application fields: `guid` (REST), `id` (legacy numeric app_id for XML/wrapper),
  `profile.{name,business_criticality,policies[].policy_compliance_status,teams[],git_repo_url,...}`.
  `policy_compliance_status` is SCREAMING_SNAKE_CASE (`DID_NOT_PASS`). **[live 2026-11-11]**
- `POST /appsec/v1/applications` with `{"profile": {"name", "business_criticality", ...}}` creates
  a profile. **[live 2026-11-11, see lab run 1 for the exact response]**
- HMAC signing: key-derivation string `vcode_request_version_1`; id lowercased with any region
  prefix stripped after the last `-`; host lowercased; method uppercased; path with query verbatim.
  An OAuth client secret in an HMAC signer fails with "Non-hexadecimal digit found". The signer
  library can put the secret into its exception text: never print a raw signing exception.
- 401 causes in CI, most likely first: OAuth credentials used as HMAC; region mismatch (API ID
  prefix `vera01e…` EU, `vera01f…` US federal); expired key; clock skew. 403 = missing role.
- Rate limits per IP: REST 500/min, XML 250/min, `detailedreport.do` 80/min; CI runners share
  the egress IP with everything else.

Tags: **[live <date>]** observed in the lab on that date; **[2026-10, not re-verified]** carried over, check before relying on it.
