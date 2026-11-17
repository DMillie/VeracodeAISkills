# Veracode on GitLab: integration options and tool pinning (reference)

Research snapshot: 2026-11-12 UTC. Web sources only. No credentials appear in this file.

## How to read this

- **docs only (read 2026-11-12)**: taken from a vendor page, script or public API response on that date. Not executed locally.
- **observed (2026-11-12)**: an HTTP status / API response seen directly (HEAD or GET), not a documented promise. Undocumented URL patterns can change without notice.
- **verified locally 2026-11-12**: executed on the demo host / the local GitLab 19.5.4 CE that day; details in `reference/integration/verified-locally.md`.
- **not confirmed** / **not reachable**: could not be established from a source; do not rely on it.
- Quotes are kept under 15 words; everything else is paraphrased.

## What this means for the pack

Preference ladder, highest first.

1. **Vendor-maintained integration (GitLab Workflow Integration).** Document as the vendor option; do not build it. It fits only if the organisation is on GitLab.com Premium/Ultimate, accepts a group-wide PAT with `api` scope held by Veracode, accepts webhooks plus a `veracode` project per group, and can live with auto-packaging and the fixed language matrix. Gating there is `veracode.yml` (`policy`, `break_build_policy_findings`), not jar flags. Self-managed support is contradictory in the docs: confirm with Veracode before recommending.
2. **Organisation-owned shared component (the direction of the pack).** Our own CI/CD component, pinned by consumers at a released version or SHA. The Veracode catalog components under `gitlab.com/veracode/veracode-components` are useful as a reference for input naming (`veracode_policy_name`, `policy_file`, `baseline_file`, `app_id`, `development_stage`) but are 0.0.x, catalog-unverified, absent from docs.veracode.com, and clone their own repo at job time. Do not depend on them directly until support status is confirmed; if used, pin by SHA.
3. **Pinned CLI/wrapper in script steps (what the component runs inside).**
   - SAST gate: `veracode/pipeline-scan` pinned by `tag@sha256:digest` (digests in `reference/integration/docker-images.md`). Use `--policy_name` for built-in policies; for custom policies run `--request_policy` then `--policy_file`; add `--baseline_file` so only new policy-violating flaws fail. Treat exit 1-200 as "findings" and 253-255 as "scan error" so the two can be handled differently.
   - Platform scans: `veracode/api-wrapper-java` pinned by digest, or the Maven Central jar at a fixed version with checksum.
   - Veracode CLI: pin with `VERACODE_CLI_VERSION`; no vendor checksum exists and old versions disappear, so mirror the tarball internally (`VERACODE_CLI_DOWNLOAD_URL`) and record our own SHA-256. CLI gate exit code is 3, not a flaw count.
   - SCA agent: pin with `SRCCLR_VERSION` (script-only, undocumented) or download the versioned tgz directly and verify the `.asc`; avoid unpinned `curl | sh` in the shared component.
4. **Raw API, agent-side only.** Keep for the onboarding agent (profile lookup, policy listing, results retrieval), never as the pipeline gate. Not researched further here.

Open items to verify locally: plain vs `cmd-` image variants; `--policy_file` combined with `--fail_on_severity`; PGP key for the SCA tgz signature.

## Where each part lives

| Part | File | Read it when |
|---|---|---|
| 1. What Veracode ships for GitLab | `reference/integration/gitlab-official-options.md` | choosing between the Workflow Integration, Veracode's catalog components and an organisation-owned component |
| 2. Policy-driven gating | `reference/integration/policy-gating.md` | making a gate follow the application's policy instead of a severity list |
| 3. Docker Hub images | `reference/integration/docker-images.md` | pinning a scanner image by tag and digest |
| 4. Veracode CLI versions | `reference/integration/cli-install.md` | installing one exact CLI version in a job |
| 5. SCA agent in CI | `reference/integration/sca-agent-ci.md` | running the SCA agent without piping an install script into a shell |
| 6. Direct downloads | `reference/integration/direct-downloads.md` | fetching the Pipeline Scan zip or the Java API wrapper by version |
| 8. Verified locally | `reference/integration/verified-locally.md` | checking whether a behaviour above was observed or only read |
