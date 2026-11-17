# GitLab-side facts that matter here

- Protected CI variables never reach merge-request or unprotected-branch pipelines: Veracode
  variables must be masked and **unprotected** for the gate to run on feature branches. [GL-01]
- `GET /projects/:id/jobs/artifacts/:ref/raw/<path>?job=<name>` serves the artifact of the latest
  **fully successful pipeline** of the ref, not of the latest successful job. With a long policy
  scan or any failing job in that pipeline the baseline is never served. The component therefore
  publishes the baseline as a **generic package** (`PUT/GET
  /projects/:id/packages/generic/veracode-baseline/<ref slug>/baseline.json`, job token, CE
  feature, project `packages_enabled`) and uses the artifact only as a fallback. [GL-02]
- `CI_API_V4_URL` is derived from the instance's external URL. Where that URL is not reachable
  from job containers, every job-token API call fails and `curl -sf` hides it. Override with a
  group/project variable `CI_API_V4_URL` pointing at the in-network hostname. [GL-03]
- A failed job in an earlier stage makes GitLab **skip** later-stage jobs that have no `needs`.
  Informational scan jobs carry `allow_failure: true`. [GL-04]
- `artifacts:reports:sast` is accepted by the parser on CE; the MR security widget that reads it
  is Ultimate-only. [GL-05]
- A file of hidden jobs only fails the lint API with "should contain at least one visible job";
  lint it with a probe job appended (`tools/gitlab-ci-lint.sh`, `GITLAB_LINT_PROBE=probe`). [GL-06]
- dind with TLS needs `DOCKER_HOST=tcp://docker:2376`, `DOCKER_TLS_CERTDIR=/certs`,
  `DOCKER_TLS_VERIFY=1`, `DOCKER_CERT_PATH=$DOCKER_TLS_CERTDIR/client` and the runner mounting
  `/certs/client`. Mounting the host docker socket breaks the dind service. [GL-07]

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
