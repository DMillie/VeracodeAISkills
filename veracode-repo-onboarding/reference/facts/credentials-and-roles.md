# Credentials and roles (names only)

- Two credential pairs can exist on one API service account: HMAC API ID/key (hex secret) and
  OAuth client id/secret. CI plugins, the wrapper, the Pipeline Scan jar and the CLI take HMAC.
- API roles seen on a working onboarding account: `uploadapi`, `submitterapi`, `apisubmitanyscan`,
  `greenlightapiuser` (Pipeline Scan), `resultsapi`, `adminapi`, `noteamrestrictionapi`,
  `mitigationapi`, `reportingApi`, `extunifiedstaticscanuser`, `archerreports`. Minimum for this
  pack: upload + submit + Pipeline Scan (+ `adminapi` or team membership to create profiles).
  [CRED-01]
- Human users cannot hold API roles; automation runs on an API service account.

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
