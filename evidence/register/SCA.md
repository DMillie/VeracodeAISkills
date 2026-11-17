# Evidence register: SCA

| ID | Basis | Checked | Source or observation | Claim as written in the skill | File |
|---|---|---|---|---|---|
| SCA-01 | carried | 2026-10 | 2026-10 | Needs a CI-type agent token in `SRCCLR_API_TOKEN`; a CLI agent's 36-character activation token is rejected; an API service account cannot create agent tokens (a user with SCA workspace rights must). | `shared/reference/facts/sca-agent.md` |
| SCA-02 | lab | 2026-11-12 | observed in the lab | Upload and Scan runs SCA on what is uploaded (bundled library jars, `composer.lock`, lockfiles in a source zip) and those results DO count in the policy verdict of the application profile: three of four first policy scans on 2026-11-12 were Did Not Pass because of library findings, not static flaws. Only the agent-based scan reports to the SCA workspace alone. | `shared/reference/facts/sca-agent.md` |
| SCA-05 | lab | 2026-11-12 | CLI directory scan on repositories with Cargo.lock and composer.lock (transitive packages reported) and on Gradle Kotlin DSL and build.sbt without lockfiles (nothing reported, job green) | The CLI directory scan reads manifests and lockfiles only | `shared/reference/facts/sca-agent.md` |
