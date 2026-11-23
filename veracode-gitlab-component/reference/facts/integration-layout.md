# Integration layout

- The pack integrates through ONE organisation-owned GitLab CI/CD component
  (`templates/gitlab/component/`, central project e.g. `platform/veracode-ci`), included by
  reference at an exact release. Vendor options and sources: `integration-options.md`.
  Components, `spec:inputs` (string/boolean/array, `options`) and `include: component:
  $CI_SERVER_FQDN/…@<exact tag>` work on self-managed GitLab CE 19.5. [LAY-01]
- Includes are resolved with the permissions of the user who triggers the pipeline: an internal
  central project is readable by every signed-in user; a private one needs membership. The job
  token is not involved. [LAY-02]
- Pinned in the component 1.0.0: `veracode/pipeline-scan:26.11.0`, `veracode/api-wrapper-java:26.10.20.1`,
  `docker:27.5.1`(+`-dind`), `alpine:3.24.4`, all `tag@sha256`; Veracode CLI 2.55.0 and SCA agent
  3.8.125 by version + SHA-256 (the agent's PGP signature verified at pin time). [LAY-03]
- Veracode publishes no checksum for the CLI tarball and removes old CLI versions from
  `tools.veracode.com`; a durable pin needs an internal mirror (`cli_download_url` input).
  [LAY-08]
- Gate criteria: Pipeline Scan `--policy_name` works only for built-in policies and
  `--request_policy` only for custom ones ("Builtin policies cannot be downloaded", exit 255).
  The application's policy name is read with the API wrapper (`GetAppList`, `GetAppInfo`:
  attribute `policy`, XML-escaped). [LAY-04]
- API wrapper `UploadAndScan` with `-scantimeout`: exit 0 = passed policy, exit 4 = scan
  completed and the application did not pass. [LAY-05]
- In `rules:if`, an unset variable is an empty string for `=~`: `$CI_COMMIT_TAG =~ /^$/` is true
  on branch pipelines. Guard with `$VAR &&`. [LAY-06]
- `allow_failure: exit_codes: [42]` gives a per-run choice between red and orange from one job
  definition; the component uses 42 as "warning". [LAY-07]

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
