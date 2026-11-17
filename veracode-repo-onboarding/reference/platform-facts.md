# Veracode platform facts for onboarding

Rules only. How each one is known (date, source, what was observed) is in the evidence register,
`evidence/` in the source repository, under the ID in brackets. No suffix: observed in the lab
(GitLab 19.5 CE, x86_64 docker runner, US commercial tenant, 2026-11). `~`: read, not run. `?`: carried
over from 2026-10 and not re-verified: check before relying on it. If today is more than six months
after 2026-11, check a fact against docs.veracode.com before relying on it.

This file is the index. Read only the topic file you need.

| Topic | File | Read it when |
|---|---|---|
| Integration layout | `reference/facts/integration-layout.md` | deciding how scanning is wired into CI (component, includes, inputs) |
| Tools and images | `reference/facts/tools-and-images.md` | choosing or pinning a scanner image, jar or CLI version |
| Pipeline Scan | `reference/facts/pipeline-scan.md` | running or reading a Pipeline Scan; the 6-per-minute limit; result file shape |
| Upload and Scan | `reference/facts/upload-and-scan.md` | sandbox or policy scans through the API wrapper; pre-scan; one open scan per profile |
| Agent-based SCA | `reference/facts/sca-agent.md` | dependency scans in CI; which package managers work |
| Veracode CLI | `reference/facts/veracode-cli.md` | `veracode package` and the CLI's scan commands |
| REST API | `reference/facts/rest-api.md` | creating or looking up an application profile |
| Credentials and roles | `reference/facts/credentials-and-roles.md` | which variable names and API roles a job needs (names only) |
| GitLab | `reference/facts/gitlab.md` | GitLab behaviour that changes the CI design (includes, job tokens, artifacts) |
