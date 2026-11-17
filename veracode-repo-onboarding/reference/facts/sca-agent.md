# Agent-based SCA

- Needs a **CI-type agent token** in `SRCCLR_API_TOKEN`; a CLI agent's 36-character activation
  token is rejected; an API service account cannot create agent tokens (a user with SCA workspace
  rights must). **[2026-10]**
- Results go to the SCA workspace/project, not to the application profile; the Findings API
  `scan_type=SCA` returns only upload-based SCA. Transitive dependencies are resolved by the
  agent; the CLI directory scan reads manifests and lockfiles: with a lockfile it reports transitive packages too (Cargo.lock, composer.lock seen 2026-11-12); without one (Gradle Kotlin DSL, build.sbt) it reported nothing and still ended green. **[2026-11-12]**
- Upload and Scan runs SCA on what is uploaded (bundled library jars, `composer.lock`, lockfiles in a source zip) and those results DO count in the policy verdict of the application profile: three of four first policy scans on 2026-11-12 were Did Not Pass because of library findings, not static flaws. Only the agent-based scan reports to the SCA workspace alone. **[live 2026-11-12]**
- Pipeline Scan API: 6 scan submissions per minute per API user, then `HTTP Response 429`. One shared service account across many pipelines hits it; component >= 1.3.1 waits and retries. **[live 2026-11-12]**
- A language Veracode Static does not analyse can still be ACCEPTED: a zipped Rust debug ELF gave `SCAN_STATUS SUCCESS`, one module, 0 findings. Zero findings on an unsupported language is no result, not a clean result. **[live 2026-11-12]**

Tags: **[live <date>]** observed in the lab on that date; **[2026-10, not re-verified]** carried over, check before relying on it.
