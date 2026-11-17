# 8. Verified locally on 2026-11-12 (demo host, x86_64; local GitLab CE 19.5.4, runner 19.5 docker executor)

| What | Result |
|---|---|
| GitLab CI/CD **components on self-managed CE with external URL `http://localhost:8929`** | work. `include: component: $CI_SERVER_FQDN/platform/veracode-ci/veracode@1.0.0` resolves (CI_SERVER_FQDN = `localhost:8929`); `spec:inputs` with string/boolean/array types, `options`, defaults; lint API and real pipelines. |
| Component version references | exact tag `@1.0.0` works. `@1.0` and `@~latest` fail with "content not found": they need a catalog-published release, and a release created through the Releases API is not one (the catalog stayed empty after `catalogResourcesCreate`). The pack pins exact tags, so nothing depends on this. |
| `include: project/ref/file` with `inputs` on the same file | works (lint valid, same 9 jobs). Kept as the documented fallback. |
| Access from `demo` (private projects) to `platform/veracode-ci` | project **internal**: a developer who is member of `demo` only lints valid. Project **private**: "project does not exist or you don't have sufficient permissions". Includes use the pipeline user's permissions; the CI job token and its allowlist are not involved. |
| Unset variables in `rules:if` regex | `$CI_COMMIT_TAG =~ /^$/` is true on branch pipelines (unset = empty string): a rehearsal branch started a policy scan. Rules in the component are guarded with `$VAR &&`. |
| `veracode/pipeline-scan:26.11.0` digest | `sha256:bde005b8…ce9a6b` (docker pull + inspect); jar reports 26.11.0-0; runs in CI by `tag@digest`. |
| `veracode/api-wrapper-java:26.10.20.1` digest | `sha256:cfdb8ea6…56ca11`; `VeracodeJavaAPI v26.10.20.1`; runs in CI by `tag@digest`. |
| `docker:27.5.1` / `docker:27.5.1-dind`, `alpine:3.24.4` | `sha256:aa3df78e…9176ce` (both docker tags are the same image), `sha256:f59abe65…8c71bf`. |
| pipeline-scan.jar `--help` | `(-f FILE | -rp REQUEST_POLICY) [-pn POLICY_NAME | -pf POLICY_FILE]`, `-bf`, `-fs`, `-fc`, `-aid`, `-ds`. |
| `--request_policy "<built-in policy>"` | fails: "Builtin policies cannot be downloaded", exit 255. Built-in policies must be applied with `--policy_name`; the component tries the download and falls back. |
| `--policy_name "Veracode Policy - Disallow High & Above"` | works: 8 flaws analysed, exit code 2 (the Very High and the High), Medium "skipped". With `--baseline_file` the exit code counts only flaws not in the baseline (lab run 3: 0 on a docs-only branch, 1 on a branch with one new flaw). |
| Custom policy path (`--request_policy` then `--policy_file`) | verified locally with the jar (not in a pipeline): a temporary custom policy with a throwaway name (MAX_SEVERITY 5) was downloaded to `policy.json` (exit 0) and applied with `--policy_file`: 1 Very High counted, the High and 6 Medium "skipped". Policy deleted afterwards. The component's end-to-end custom path (policy assigned to a profile, resolved by `veracode-policy-resolve`) ran only in the stubbed logic test. |
| Policy of an application profile through the official wrapper | `-action GetAppList` (app id by name) then `-action GetAppInfo -appid` returns `<application … policy="…">` (XML-escaped `&amp;`). Used by job `veracode-policy-resolve`. |
| Veracode CLI pin | `veracode-cli_2.55.0_linux_x86.tar.gz` SHA-256 `44fde332acc9401f51486404dba3289cff894cf32aafda612e0a8f1cbc1b2140` (computed by us: trust on first use; no vendor checksum). The binary runs on Alpine 3.24 (busybox `wget` and `sha256sum` are enough; no `apk add`). |
| SCA agent pin | `srcclr-3.8.125-linux.tgz` SHA-256 `cff73912…53d6fa`, `…-linux_musl_x64.tgz` `8d413d9c…008355`. `gpg --verify` of `srcclr-3.8.125-linux.tgz.asc` with the key from `https://sca-downloads.veracode.com/redhat/SRCCLR-GPG-KEY`: **Good signature**, primary key fingerprint `2B93 609D A5A4 9D7F 2082 246F DF7D D7A5 0B74 6DD4` ("Production (Official Key) <production@srcclr.com>"). The key is fetched from the same host as the archive, so the fingerprint is pinned in `tools/pin-versions.sh`. |
| SCA agent without `ci.sh` | download tgz by version, `sha256sum -c`, untar, `bin/srcclr scan --allow-dirty`: works in `python:3.11` and `maven:3.9-eclipse-temurin-17` (lab run 3, lab run 4). |
| Veracode GitLab Workflow Integration | **not installed, not tested** (out of scope by instruction; documented in section 1a only). |

Index and reading guide: `reference/integration-options.md`.
