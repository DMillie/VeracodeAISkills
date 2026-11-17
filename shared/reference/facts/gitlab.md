# GitLab-side facts that matter here

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

Tags: **[live <date>]** observed in the lab on that date; **[2026-10, not re-verified]** carried over, check before relying on it.
