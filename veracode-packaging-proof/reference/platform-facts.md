# Veracode platform facts for onboarding

Tags: **[live 2026-11-11]** observed on this rebuild (US commercial tenant, GitLab 19.5 CE,
x86_64 docker runner); **[2026-10, not re-verified]** carried over from an earlier 2026-10 pack
(arm64 runner); treat as likely but check before relying on it. Re-check anything
older than six months.

## Integration layout (2026-11-12)

- The pack integrates through ONE organisation-owned GitLab CI/CD component
  (`templates/gitlab/component/`, central project e.g. `platform/veracode-ci`), included by
  reference at an exact release. Vendor options and sources: `integration-options.md`.
  Components, `spec:inputs` (string/boolean/array, `options`) and `include: component:
  $CI_SERVER_FQDN/…@1.0.0` work on self-managed GitLab CE 19.5.4 whose external URL is
  `http://localhost:8929`. **[live 2026-11-12]**
- Includes are resolved with the permissions of the user who triggers the pipeline: an internal
  central project is readable by every signed-in user; a private one needs membership. The job
  token is not involved. **[live 2026-11-12]**
- Pinned in the component 1.0.0: `veracode/pipeline-scan:26.11.0`, `veracode/api-wrapper-java:26.10.20.1`,
  `docker:27.5.1`(+`-dind`), `alpine:3.24.4`, all `tag@sha256`; Veracode CLI 2.55.0 and SCA agent
  3.8.125 by version + SHA-256 (the agent's PGP signature verified at pin time). **[live 2026-11-12]**
- Veracode publishes no checksum for the CLI tarball and removes old CLI versions from
  `tools.veracode.com`; a durable pin needs an internal mirror (`cli_download_url` input).
  **[docs/observed 2026-11-12, mirror not built]**
- Gate criteria: Pipeline Scan `--policy_name` works only for built-in policies and
  `--request_policy` only for custom ones ("Builtin policies cannot be downloaded", exit 255).
  The application's policy name is read with the API wrapper (`GetAppList`, `GetAppInfo`:
  attribute `policy`, XML-escaped). **[live 2026-11-12; custom path verified with the jar locally (temporary policy with a throwaway name), not in a pipeline]**
- API wrapper `UploadAndScan` with `-scantimeout`: exit 0 = passed policy, exit 4 = scan
  completed and the application did not pass. **[live 2026-11-11/12]**
- In `rules:if`, an unset variable is an empty string for `=~`: `$CI_COMMIT_TAG =~ /^$/` is true
  on branch pipelines. Guard with `$VAR &&`. **[live 2026-11-12]**
- `allow_failure: exit_codes: [42]` gives a per-run choice between red and orange from one job
  definition; the component uses 42 as "warning". **[live 2026-11-12]**

## Tools and images

- `veracode/pipeline-scan` (pinned `26.11.0@sha256:…` in the component; facts first observed on `latest`): Alpine, OpenJDK 11, jar at `/opt/veracode/pipeline-scan.jar`;
  `curl`, `wget`, `zip`, `unzip` present. **[live 2026-11-11]**
- `veracode/api-wrapper-java` (pinned `26.10.20.1@sha256:…`): Alpine, jar at `/opt/veracode/api-wrapper.jar`
  (`-action UploadAndScan` etc.); `curl` present. **[live 2026-11-11]**
- Both images run as **uid 1000 (`luser`)**. GitLab Runner 19.5 (docker executor) reuses a build
  volume per concurrency slot; when a root-image job created the checkout directory (root, 0755)
  a later job in these images could not write `results.json` on that slot ("Permission denied";
  intermittent, slot-dependent). The component runs these jobs with `image:docker:user: root`.
  **[live 2026-11-11]**
- No official `veracode/veracode-cli` image on Docker Hub (pull denied). The component downloads
  `veracode-cli_<version>_linux_x86.tar.gz` and checks its SHA-256 instead of piping Veracode's
  install script into a shell. That script (`…/veracode-cli/install`, honours
  `VERACODE_CLI_VERSION`) writes `./veracode` into the
  **current directory**, so install outside the tree you will scan (a directory scan of `.` after
  installing there reported the CLI's own Go modules: docker, golang.org/x/net, stdlib…). Works on
  Alpine 3 (`docker:27`) and installs 2.55.0. **[live 2026-11-11]**
- SCA agent: the component downloads `srcclr-<version>-linux[_musl_x64].tgz`, checks the SHA-256
  and runs `bin/srcclr scan`; it does not execute `ci.sh`. For reference, the bootstrap
  `https://download.sourceclear.com/ci.sh` (= `sca-downloads.veracode.com/ci.sh`, honours
  `SRCCLR_VERSION`, verifies nothing): downloads the agent to
  `$CACHE_DIR/srcclr` (default `/tmp`), runs `scan --allow-dirty` when given no arguments, appends
  `--json` when `SRCCLR_CI_JSON=1`, refuses non-x86_64 Linux. Needs `curl` and the project's
  package manager in the image. **[live 2026-11-11, script read; scan verified in CI, see lab run 1]**
- All four are x86_64-only; on arm64 runners use `amd64/` images with platform `linux/amd64`.
  A multi-arch tag pulled for arm64 broke the next amd64 pull on a shared daemon. **[2026-10]**
- The CLI's credential check timed out under emulation and still exited 0: check output files,
  not exit codes. **[2026-10]**

## Pipeline Scan

- `pipeline-scan.jar` flags (underscores): `--veracode_api_id/--veracode_api_key`, `--file`,
  `--fail_on_severity "Very High, High"`, `--baseline_file`, `--json_output_file`,
  `--filtered_json_output_file`, `--summary_output_file`, `--project_name/--project_url/--project_ref`,
  `--gl_vulnerability_generation true` (writes `veracode_gitlab_vulnerabilities.json`), `--timeout`
  minutes, `--development_stage {Development,Testing,Release}`, `--include`. **[live 2026-11-11, --help]**
- Exit code = number of flaws matching the fail criteria (1–200); 0 none; other values are
  errors. The CLI's `veracode static scan` exits 3 on matching flaws instead. **[2026-10]**
- Results are kept by Veracode for 24 hours only: keep `results.json` as a job artifact. **[2026-10]**
- Results never reach the Findings API or the application profile; compliance needs a policy scan.
- Severity in `results.json`: `findings[].severity` integer 5..0 (Very High..Informational),
  `cwe_id` string, `issue_type`, `files.source_file.{file,line}`. **[live 2026-11-11, see lab run 1]**
- `--fail_on_severity` takes English strings; the REST APIs take integers. Both are right.

## Upload and Scan (policy and sandbox) via the API wrapper

- `-action UploadAndScan -vid -vkey -appname -createprofile {true,false} -filepath -version
  -autoscan true -deleteincompletescan 1 [-scantimeout minutes] [-sandboxname -createsandbox true]`.
  **[live 2026-11-11, -help]**
- Without a sandbox name it is a policy scan and replaces the compliance verdict. Only one
  policy scan can be open per profile; a stuck one blocks uploads unless `-deleteincompletescan 1`
  (which did not clear a build stuck at Pre-Scan Success after a fatal pre-scan; that needed
  `DeleteBuild`). **[2026-10]**
- `-createprofile true` with a misspelled app name silently creates a new empty profile; keep it
  false and create the profile via the REST API by exact name. The 2026-10 note that the flag
  must be present even for existing profiles is why the templates always pass it. **[2026-10]**
- Without `-scantimeout` the job returns after the upload: "accepted upload" is not "completed
  scan". With it the wrapper polls and fails the job if the scan does not pass policy.
- Per-branch sandbox names hit the per-application sandbox limit fast; one per long-lived branch.

## Agent-based SCA

- Needs a **CI-type agent token** in `SRCCLR_API_TOKEN`; a CLI agent's 36-character activation
  token is rejected; an API service account cannot create agent tokens (a user with SCA workspace
  rights must). **[2026-10]**
- Results go to the SCA workspace/project, not to the application profile; the Findings API
  `scan_type=SCA` returns only upload-based SCA. Transitive dependencies are resolved by the
  agent; the CLI directory scan reads manifests and lockfiles: with a lockfile it reports transitive packages too (Cargo.lock, composer.lock seen 2026-11-12); without one (Gradle Kotlin DSL, build.sbt) it reported nothing and still ended green. **[2026-11-12]**
- Upload and Scan runs SCA on what is uploaded (bundled library jars, `composer.lock`, lockfiles in a source zip) and those results DO count in the policy verdict of the application profile: three of four first policy scans on 2026-11-12 were Did Not Pass because of library findings, not static flaws. Only the agent-based scan reports to the SCA workspace alone. **[live 2026-11-12]**
- Pipeline Scan API: 6 scan submissions per minute per API user, then `HTTP Response 429`. One shared service account across many pipelines hits it; component >= 1.3.1 waits and retries. **[live 2026-11-12]**
- A language Veracode Static does not analyse can still be ACCEPTED: a zipped Rust debug ELF gave `SCAN_STATUS SUCCESS`, one module, 0 findings. Zero findings on an unsupported language is no result, not a clean result. **[live 2026-11-12]**

## Veracode CLI (2.55.0)

- `veracode scan --type directory --source . --format table --output file.txt` writes the table
  to the file and only INF lines to stdout; `cat` the file in CI. Uses the HMAC credentials from
  `VERACODE_API_KEY_ID/SECRET`; no agent token. On a Flask 1.1.2 app it reported 40 rows
  (CRITICAL..MEDIUM) from the pinned requirements. **[live 2026-11-11]**
- `veracode scan --type image --source name:tag` scans from the docker daemon; a `docker save`
  tarball read as empty and clean. **[2026-10]**
- The CLI ignored `~/.veracode/credentials` in the documented `[default]` ini form and said
  "credentials undefined"; it works with the two environment variables exported. **[live 2026-11-11]**
- `veracode static scan` (Pipeline Scan through the CLI) uses hyphenated flags
  (`--fail-on-severity`, `--baseline-file`, `--results-file`); exit 3 on matching flaws.

## REST API (application profiles)

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

## Credentials and roles (names only)

- Two credential pairs can exist on one API service account: HMAC API ID/key (hex secret) and
  OAuth client id/secret. CI plugins, the wrapper, the Pipeline Scan jar and the CLI take HMAC.
- API roles seen on a working onboarding account: `uploadapi`, `submitterapi`, `apisubmitanyscan`,
  `greenlightapiuser` (Pipeline Scan), `resultsapi`, `adminapi`, `noteamrestrictionapi`,
  `mitigationapi`, `reportingApi`, `extunifiedstaticscanuser`, `archerreports`. Minimum for this
  pack: upload + submit + Pipeline Scan (+ `adminapi` or team membership to create profiles).
  **[live 2026-11-11 account listing; minimum set not isolated]**
- Human users cannot hold API roles; automation runs on an API service account.

## GitLab-side facts that matter here

- Protected CI variables never reach merge-request or unprotected-branch pipelines: Veracode
  variables must be masked and **unprotected** for the gate to run on feature branches.
  **[live 2026-11-11]**
- `GET /projects/:id/jobs/artifacts/:ref/raw/<path>?job=<name>` with `JOB-TOKEN` serves the
  artifact of the latest **fully successful pipeline** of the ref, not of the latest successful
  job: with a 30-minute policy scan or a failing job in the same pipeline the baseline was never
  served (lab run 1, pipeline 68). The templates therefore publish the baseline as a **generic
  package** (`PUT/GET /projects/:id/packages/generic/veracode-baseline/<ref slug>/baseline.json`,
  job token, CE feature, project `packages_enabled`) and use the artifact only as a fallback.
  Publish (201) and fetch (200) with the job token verified; gate then reported "0 new flaws".
  **[live 2026-11-11]**
- `CI_API_V4_URL` is derived from the instance's external URL. On a self-managed instance whose
  external URL is not reachable from job containers (this demo: `localhost`), every job-token API
  call fails; `curl -sf` hides it. Override with a group/project variable `CI_API_V4_URL` pointing
  at the in-network hostname (group variables beat the predefined value). **[live 2026-11-11]**
- A failed job in an earlier stage makes GitLab **skip** later-stage jobs that have no `needs`:
  a red informational scan job skipped the team's own `build` job. Informational scan jobs carry
  `allow_failure: true`. **[live 2026-11-11]**
- `artifacts:reports:sast` is accepted by the parser on CE; the MR security widget that reads it
  is Ultimate-only. **[live 2026-11-11, lint]**
- A file of hidden jobs only fails the lint API with "should contain at least one visible job";
  lint it with a probe job appended (`tools/gitlab-ci-lint.sh`, `GITLAB_LINT_PROBE=probe`).
  **[live 2026-11-11]**
- dind with TLS needs `DOCKER_HOST=tcp://docker:2376`, `DOCKER_TLS_CERTDIR=/certs`,
  `DOCKER_TLS_VERIFY=1`, `DOCKER_CERT_PATH=$DOCKER_TLS_CERTDIR/client` and the runner mounting
  `/certs/client`. Mounting the host docker socket breaks the dind service. **[live 2026-11-11]**
