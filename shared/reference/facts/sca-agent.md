# Agent-based SCA

- Needs a **CI-type agent token** in `SRCCLR_API_TOKEN`. A CLI agent's 36-character activation
  token is rejected. An API service account cannot create agent tokens: a user with SCA
  workspace rights must. [SCA-01?]
- Agent results go to the SCA workspace/project, not to the application profile; the Findings
  API `scan_type=SCA` returns only upload-based SCA.
- The agent resolves transitive dependencies. The CLI directory scan reads manifests and
  lockfiles only: with a lockfile it reports transitive packages too; without one it reports
  nothing and still ends green. [SCA-05]
- Upload and Scan runs SCA on what is uploaded (bundled library jars, lockfiles in a source zip)
  and those results DO count in the policy verdict of the application profile. A first policy
  scan can be Did Not Pass because of library findings alone. [SCA-02]

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
