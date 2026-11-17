# Veracode on GitLab: integration options and tool pinning (reference)

Research snapshot: 2026-11-12 UTC. Web sources only. No credentials appear in this file.

## How to read this

- **docs only (read 2026-11-12)**: taken from a vendor page, script or public API response on that date. Not executed locally.
- **observed (2026-11-12)**: an HTTP status / API response seen directly (HEAD or GET), not a documented promise. Undocumented URL patterns can change without notice.
- **verified locally 2026-11-12**: executed on the demo host / the local GitLab 19.5.4 CE that day; details in section 8.
- **not confirmed** / **not reachable**: could not be established from a source; do not rely on it.
- Quotes are kept under 15 words; everything else is paraphrased.

## 1. What Veracode officially ships for GitLab

### 1a. GitLab Workflow Integration (vendor-maintained; also called Repository Scanning)

| Fact | Source | Marker |
|---|---|---|
| Runs Pipeline Scan (SAST), SCA agent-based scan and Container/IaC/secrets scans across repositories. Page last updated Oct 22, 2026. | https://docs.veracode.com/r/GitLab_Workflow_Integration | docs only (read 2026-11-12) |
| Installed from the Veracode Platform (Repository Scan > Add SCM integration > GitLab), not from GitLab. On install Veracode creates a `veracode` project in each selected group and adds webhooks to the groups. | same | docs only (read 2026-11-12) |
| The `veracode` project holds the workflow templates plus `veracode.yml` (scan settings) and `repo_list.yml` (`include_repos` / `exclude_repos`). Pipelines and results appear in the `veracode` project (Build > Pipelines), artifacts in `veracode-artifact`. | same | docs only (read 2026-11-12) |
| Default behaviour: scans every repository in the groups where installed, on push/merge activity on any branch, except the `veracode` project itself. | same | docs only (read 2026-11-12) |
| `veracode.yml` keys include: `push.trigger`, `branches_to_run`, `branches_to_exclude`, `pull_request.trigger/action/target_branch`, `analysis_branch`, `analysis_on_platform` (default false), `break_build_policy_findings` (default true), `break_build_invalid_policy`, `break_build_on_error`, `policy` (default 'Veracode Recommended Medium + SCA'), `create_issue`, `create_code_scanning_alert`, `issues.trigger/commands`, `filter_mitigated_flaws`, `profile`, `debug`. | same | docs only (read 2026-11-12) |
| With `analysis_on_platform: true`: MR to `analysis_branch` runs a sandbox scan; merge into it runs a policy scan. Auto-created profile name format `GITLAB/{Group}/{repository}`. | same | docs only (read 2026-11-12) |
| Supported only on GitLab.com Premium and Ultimate. The page states it is not supported on GitLab Dedicated or Self-Managed. | same | docs only (read 2026-11-12) |
| Prerequisites: Veracode Administrator or Security Lead role; GitLab Owner role; Veracode API credentials; SCA agent token (for SCA); a GitLab personal access token with `api` scope from a user with access to all target groups. | same | docs only (read 2026-11-12) |
| Limits: Linux runners only (with `wget`, Java API wrapper requirements); not available in the US Federal region; non-US-keyboard characters in repo name/description can break scans; runner must reach Veracode domains/IPs. | same | docs only (read 2026-11-12) |
| Auto-packaging is the default build path; language/version matrix is fixed (e.g. Java 21+, Gradle 8.7, .NET 6-8, Go 1.22.4). | same | docs only (read 2026-11-12) |
| A separate "GitLab Self-Managed Workflow Integration" page exists (HTTP 200) describing the same model for self-managed servers, with a `default: runs_on` runner setting in `veracode.yml` and a service-account PAT with `api` scope. It is not listed in the docs sitemap and contradicts the "not supported on Self-Managed" sentence on the main page. Treat self-managed availability as **not confirmed**; ask Veracode. | https://docs.veracode.com/r/GitLab_Self_Managed_Workflow_Integration ; https://docs.veracode.com/sitemap.xml | docs only (read 2026-11-12) |
| A search-engine snippet claimed the integration must be enabled by Veracode Support and is US Commercial region only. Neither sentence is on the current page. | (search snippet, older page version) | not confirmed |
| Repository Scanning can feed Veracode Risk Manager; that add-on is enabled on request via a customer success representative. | https://docs.veracode.com/r/Integrate_with_Veracode_Repository_Scanning | docs only (read 2026-11-12) |
| Local set-up of the Workflow Integration | - | out of scope (we will not set it up) |

### 1b. GitLab CI/CD Catalog components (published by the `veracode` GitLab group)

Catalog search for "veracode" (GitLab GraphQL `ciCatalogResources`) returned 8 resources, all under `gitlab.com/veracode/veracode-components`, all with verification level **UNVERIFIED** (no GitLab "verified creator" badge).

| Component | Latest release (date) | Source | Marker |
|---|---|---|---|
| veracode-pipeline-scan | 0.0.109 (2026-09-01) | https://gitlab.com/veracode/veracode-components/veracode-pipeline-scan | observed (2026-11-12) |
| veracode-packaging | 0.0.19 (2026-09-01) | https://gitlab.com/veracode/veracode-components/veracode-packaging | observed (2026-11-12) |
| veracode-uploadandscan | 0.0.21 (2026-09-01) | https://gitlab.com/veracode/veracode-components/veracode-uploadandscan | observed (2026-11-12) |
| veracode-sca | 0.0.1 (2026-08-31) | https://gitlab.com/veracode/veracode-components/veracode-sca | observed (2026-11-12) |
| veracode-iac-secrets-scan | 0.0.5 (2026-09-11) | https://gitlab.com/veracode/veracode-components/veracode-iac-secrets-scan | observed (2026-11-12) |
| veracode-dast | 0.0.1 (2026-09-02) | https://gitlab.com/veracode/veracode-components/veracode-dast | observed (2026-11-12) |
| veracode-fix | v0.0.9 (2025-04-19) | https://gitlab.com/veracode/veracode-components/veracode-fix | observed (2026-11-12) |
| veracode-findings-to-issues | v0.0.18 (2025-03-21) | https://gitlab.com/veracode/veracode-components/veracode-findings-to-issues | observed (2026-11-12) |

| Fact | Source | Marker |
|---|---|---|
| The `veracode` GitLab group describes itself as "Veracode's open-source offerings" (created 2016). | https://gitlab.com/groups/veracode | observed (2026-11-12) |
| These components are **not mentioned on docs.veracode.com** (no sitemap page for components/catalog). Support status ("official, supported product" vs open-source/community) is **not confirmed**. All versions are 0.0.x; tag naming changed from `v0.0.N` to `0.0.N`. | https://docs.veracode.com/sitemap.xml | docs only (read 2026-11-12) |
| veracode-pipeline-scan template (main): default image `veracode/scm-packaging:5.0.0`; inputs include `vid`, `vkey`, `artifactsfolder`, `veracode_policy_name` (default 'Veracode Recommended Medium + SCA'), `policy_file`, `fail_on_severity`, `fail_on_cwe`, `baseline_file`, `app_id`, `development_stage`, `store_baseline_file`, `allow_failure`; `fail_build` is documented in the template as not enforced. | https://gitlab.com/veracode/veracode-components/veracode-pipeline-scan/-/blob/main/templates/veracode-pipeline-scan.yml | docs only (read 2026-11-12) |
| At job time the component git-clones its own repo from `$CI_SERVER_HOST/veracode/veracode-components/...`, checks out the component SHA and runs a compiled Node script. Consequence: it needs network access to that project path on the same GitLab host; on self-managed that path would have to be mirrored. Job rules are fixed to push and merge-request pipelines. | same | docs only (read 2026-11-12) |
| Behaviour of the component in our pipelines | - | verified locally 2026-11-12 (section 8; lab run 3, lab run 4) |

### 1c. Official CI templates / examples

| Fact | Source | Marker |
|---|---|---|
| Docs give copy-paste `.gitlab-ci.yml` examples for pipeline-scan.jar (plain, issue generation, SAST report import, built-in policy). They download `pipeline-scan-LATEST.zip`; docs recommend switching to the Docker image "for improved stability". | https://docs.veracode.com/r/Example_code_for_GitLab | docs only (read 2026-11-12) |
| Importing findings as GitLab vulnerabilities needs Premium/Ultimate; issue generation works on any tier and needs a PAT with `api` scope in CI variable `PRIVATE_TOKEN`; `GITLAB_URL` overrides the API base for custom domains. | https://docs.veracode.com/r/Configure_Pipeline_Scan_setings | docs only (read 2026-11-12) |
| Veracode CLI GitLab example: `curl ... /veracode-cli/install \| sh` then `./veracode static scan <artifact>`; credentials via `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET`. | https://docs.veracode.com/r/veracode_cli_static_analysis_integration | docs only (read 2026-11-12) |
| No includable template project named "veracode-gitlab-ci-templates" found under the `veracode` group; other `veracode-*` GitLab groups/projects in search results are personal or demo namespaces. | https://gitlab.com/api/v4/projects?search=veracode | observed (2026-11-12) |
| `docs.veracode.com/r/GitLab` is the Risk Manager connector page, not a CI integration. | https://docs.veracode.com/r/GitLab | docs only (read 2026-11-12) |

## 2. Policy-driven gating: pipeline-scan.jar and Veracode CLI

Source for the jar table: https://docs.veracode.com/r/Pipeline_Scan_parameters (page last updated Feb 24, 2026).

| Parameter | What the docs say | Marker |
|---|---|---|
| `--request_policy` / `-rp` | Downloads the named policy as a file into the working directory. No scan runs. Needed for custom policies. Docs advise not downloading on every build. | docs only (read 2026-11-12) |
| `--policy_file` / `-pf` | Applies a local policy file (the one produced by `--request_policy`) to the results. | docs only (read 2026-11-12) |
| `--policy_name` / `-pn` | Applies a policy by name; "You can only use this parameter with a default policy" (i.e. built-in policies). | docs only (read 2026-11-12) |
| `--fail_on_severity` / `-fs` | Comma-separated severities. Default is all five severities. | docs only (read 2026-11-12) |
| `--fail_on_cwe` / `-fc` | Comma-separated CWE IDs. Default all CWEs. If used alone, the default severity list still applies. | docs only (read 2026-11-12) |
| `--baseline_file` / `-bf` | Filters out flaws present in the baseline; only new flaws are reported. | docs only (read 2026-11-12) |
| `--app_id` / `-aid` | Exists. Application profile ID for the scan. | docs only (read 2026-11-12) |
| `--development_stage` / `-ds` | Exists. Case-sensitive: `Development`, `Testing`, `Release`. | docs only (read 2026-11-12) |
| Output | `--json_output_file` (default `results.json`), `--filtered_json_output_file` (default `filtered_results.json`, must differ), `--summary_output`, `--issue_details`, `--gl_issue_generation`, `--gl_vulnerability_generation`. | docs only (read 2026-11-12) |
| Other | `--timeout` (default and max 60 min), `--include`, `--project_name/_url/_ref`, `--emit_stack_dump`, `--veracode_profile`. | docs only (read 2026-11-12) |
| Actual `--help` output of the pinned jar | - | verified locally 2026-11-12 (section 8) |

| Fact | Source | Marker |
|---|---|---|
| In the GitLab example, `--policy_name` "replaces the --fail_on_severity and --fail_on_cwe parameters". | https://docs.veracode.com/r/Example_code_for_GitLab | docs only (read 2026-11-12) |
| Policy + baseline: define criteria by severity/CWE or by `--policy_file`/`--policy_name`, add `-bf`; the stage fails only for flaws matching the criteria that are not in the baseline; passes if none match or all are in the baseline. | https://docs.veracode.com/r/r_pipeline_scan_examples | docs only (read 2026-11-12) |
| Policy rule types honoured: findings by CWE ID, by CWE category, by severity. Grace periods, scan frequency and evaluation time frames are not considered. | https://docs.veracode.com/r/Configure_Pipeline_Scan_setings | docs only (read 2026-11-12) |
| Baseline can only be produced by Pipeline Scan (a renamed `results.json`), not from the Platform; docs advise versioning it next to the app. Pipeline Scan has no mitigations or flaw matching. | https://docs.veracode.com/r/Pipeline_Scan | docs only (read 2026-11-12) |
| Exit/status codes: 0 = no flaws; 1-200 = number of flaws (capped at 200); -1/255 = failure (network, credentials, other); -2/254 = default 60-min timeout; -3/253 = `--timeout` exceeded. | https://docs.veracode.com/r/Pipeline_Scan (Status codes) | docs only (read 2026-11-12) |
| Rate/time limits: six pipeline scans per minute per user (HTTP 429 beyond that); 60 minutes max per scan. | https://docs.veracode.com/r/Pipeline_Scan | docs only (read 2026-11-12) |
| Whether a combination of `--policy_file` and `--fail_on_severity` is merged or one wins | - | not verified locally (the jar help lists `-pn` and `-pf` as mutually exclusive; the combination with `-fs` was not run) |

Veracode CLI equivalents (https://docs.veracode.com/r/veracode_static_scan, last updated Feb 4, 2026):

| Fact | Source | Marker |
|---|---|---|
| `veracode static scan <file>` runs a Pipeline Scan. Flags: `--baseline-file`, `--fail-on-cwe`, `--fail-on-severity`, `--policy-file`, `--results-file` (default `./results.json`), `--summary-output`, `--include`, `--app-id`, `--development-stage`, `--project-name/-ref/-url`, `--gl-issue-generation`, `--gl-vulnerability-generation`. | https://docs.veracode.com/r/veracode_static_scan | docs only (read 2026-11-12) |
| No `--policy-name` flag is documented for `static scan`. Policy files come from `veracode policy get "<policy_name>"` (built-in or custom; name must not contain `/`, `\` or `+`). | https://docs.veracode.com/r/veracode_policy | docs only (read 2026-11-12) |
| Exit codes: 0 success; 1 generic error; 2 parser error; 3 scan completed but "did not pass policy"; 4-7 packaging; 125-130 system. Note this differs from the jar (flaw count). | https://docs.veracode.com/r/CLI_exit_codes | docs only (read 2026-11-12) |
| CLI v2.53.0 release notes mention a new `veracode scan static` command; its flags were not reviewed. | https://docs.veracode.com/updates/r/Veracode_CLI_Updates | docs only (read 2026-11-12); details not confirmed |
| Actual CLI `--help` for the pinned version | - | not verified locally (the component does not use `veracode static scan`) |

## 3. Docker Hub images (namespace `veracode`)

Repositories listed by the Docker Hub API (7): `pipeline-scan`, `api-wrapper-java`, `scm-packaging`, `api-signing`, `vrm-runtime-agent`, `vulnerable-verademo-java`, `vulnerable-verademo-dotnet`. `veracode/veracode-cli` and `veracode/scm-integration` returned "object not found". No SCA agent (srcclr) image exists in this namespace.
Source: https://hub.docker.com/v2/repositories/veracode/?page_size=100 - observed (2026-11-12).

Digests below are the tag digests reported by the Docker Hub API (amd64). Verify with `docker pull <repo>@<digest>` before pinning: **verified locally 2026-11-12** for the four pinned images (section 8).

`veracode/pipeline-scan` (168 tags; each version has `X.Y.Z` and `cmd-X.Y.Z`; floating `latest` and `cmd`). Source: https://hub.docker.com/v2/repositories/veracode/pipeline-scan/tags?page_size=25

| Tag | Pushed | Digest | Marker |
|---|---|---|---|
| 26.11.0 (= latest) | 2026-11-10 | sha256:bde005b807ceb2f6f0439f5f0fa79a5fdcb0284abc9cf8d0919a3fafffce9a6b | observed (2026-11-12) |
| cmd-26.11.0 (= cmd) | 2026-11-10 | sha256:931cff70ad1bb0a8a8000b2c24a6645bf50a38ef2b714bc1faf567b7a1a6c0d6 | observed (2026-11-12) |
| 26.9.0 | 2026-09-23 | sha256:65d29e457b16e25e535658e40405dda6e19895576e19aad13fd5d930566bcf83 | observed (2026-11-12) |
| cmd-26.9.0 | 2026-09-23 | sha256:894fd6d68bb2b2177f1a6931806be426e547ec627a5e750e3d938b23752676da | observed (2026-11-12) |
| 26.7.0 | 2026-07-29 | sha256:282f1effbebd07a26a025ce364803bed755b90cc5066284791c5064320c25abf (index) | observed (2026-11-12) |
| 26.3.0 | 2026-03-02 | sha256:e896c7b21dc542ca7bf9e1924defb3f39cdd062dc26e1ed29a95ed150cc6fd92 (index) | observed (2026-11-12) |
| 26.2.1 | 2026-02-23 | sha256:6323606a7f50f87e8f435b13e248967f21370ac8b65032627a7f92fcfbe7bf62 (index) | observed (2026-11-12) |
| 25.8.2 | 2025-09-15 | sha256:029aaeb459a05273c83bfa9d106ff7a212967756879b941455413ea66869a5e2 | observed (2026-11-12) |

Older tags seen: 26.2.0, 25.8.1, 25.8.0, 25.7.1, 25.7.0, 25.2.0. 26.11.0 was pushed two days before this snapshot; consider 26.9.0 if a soak period is wanted. Difference between plain and `cmd-` variants (entrypoint) is **not confirmed**: local verification: TODO.

`veracode/api-wrapper-java` (90 tags; same `X` / `cmd-X` scheme). Source: https://hub.docker.com/v2/repositories/veracode/api-wrapper-java/tags?page_size=25

| Tag | Pushed | Digest | Marker |
|---|---|---|---|
| 26.10.20.1 (= latest) | 2026-10-09 | sha256:cfdb8ea641a0b5b160afc3920d1995deeb722fb902b5c5e79cf6a711cc56ca11 | observed (2026-11-12) |
| cmd-26.10.20.1 (= cmd) | 2026-10-09 | sha256:533b97a187f9706e46009eeb67cacd9afea2f02126ffc871e2515843eec6aa2a | observed (2026-11-12) |
| 26.10.20.0 | 2026-10-07 | sha256:df6a9e01cd30f478129e6edcd2275b3f911c378977aa396506c9e8a3c6aed817 | observed (2026-11-12) |
| 26.3.19.0.2 | 2026-09-11 | sha256:4838b7454deb9f96a26d808e214a1171195bf3234a62ee4c7dea4d2dce4659a1 | observed (2026-11-12) |
| 26.3.19.0 | 2026-03-18 | sha256:89b744a72313159aef6711c3a5c8a88358dc21649050651ed23be97448b7f3c7 (index) | observed (2026-11-12) |
| 26.2.18.0 | 2026-02-10 | sha256:75b70c2b0e47c3e16548c29e648f18b5eaa65b58d0142977f221b9980e1361bc (index) | observed (2026-11-12) |
| 25.11.17.0 | 2025-11-18 | sha256:53b1c780e9a764cb7682fa2a65f73a8b87b32040a235352811c4a23d2dfbdf50 | observed (2026-11-12) |

`veracode/scm-packaging` (8 tags; image used by Repository Scanning and by the catalog components): 5.0.0 (= latest, 2026-07-30) sha256:a03dec89dbf36e5db3a563a27f6ff01343793c94c137f920ca2e8fe6d517e3de; 4.0.0 (2026-04-27) sha256:e30400cae51641530c54e437374e63f04469c90335b5d5a9b92533e9c1569d9a; 3.0.0, 2.1.0, 2.0.0, 1.0.1, 1.0.0. Source: https://hub.docker.com/v2/repositories/veracode/scm-packaging/tags - observed (2026-11-12).

## 4. Veracode CLI: installing a specific version

| Fact | Source | Marker |
|---|---|---|
| Latest version: `LATEST_VERSION` returns **2.55.0**; release notes show v2.55.0 dated November 5, 2026 (v2.54.1 Oct 27, v2.54.0 Oct 23, v2.53.0 Oct 13). | https://tools.veracode.com/veracode-cli/LATEST_VERSION ; https://docs.veracode.com/updates/r/Veracode_CLI_Updates | observed / docs only (read 2026-11-12) |
| Documented pin: `curl -fsS https://tools.veracode.com/veracode-cli/install \| VERACODE_CLI_VERSION=<version> sh`. Veracode recommends always using the latest. | https://docs.veracode.com/r/Install_a_specific_version_of_the_CLI | docs only (read 2026-11-12) |
| Install script honours `VERACODE_CLI_VERSION` (else reads `LATEST_VERSION`) and `VERACODE_CLI_DOWNLOAD_URL` (alternate base URL, e.g. an internal mirror). | https://tools.veracode.com/veracode-cli/install | docs only (read 2026-11-12) |
| Download pattern used by the script: `https://tools.veracode.com/veracode-cli/veracode-cli_<version>_<suffix>.tar.gz`, suffix `linux_x86`, `macosx_x86` or `macosx_arm64`. Linux is x86_64 only. | same | docs only (read 2026-11-12) |
| The script pipes the tarball straight into `tar` and runs the bundled `install.sh`. It performs **no checksum or signature verification**. | same | docs only (read 2026-11-12) |
| No checksum/signature files found: `.sha256`, `.sig`, `.asc`, `checksums.txt` next to the 2.55.0 tarball all return 404. Published checksums: **not confirmed** (none found). | https://tools.veracode.com/veracode-cli/veracode-cli_2.55.0_linux_x86.tar.gz.sha256 (404) | observed (2026-11-12) |
| Versioned tarballs reachable (HTTP 200): 2.55.0, 2.54.0, 2.53.0, 2.52.0, 2.51.0, 2.50.0, 2.45.0. 2.40.0 and 2.35.0 return 404, so old versions are removed; a pin needs an internal mirror to stay reproducible. | https://tools.veracode.com/veracode-cli/veracode-cli_2.55.0_linux_x86.tar.gz | observed (2026-11-12) |
| Other channels: Homebrew `veracode-cli@<version>` (at most four versions behind latest), Chocolatey `--version`, signed Windows MSI, PowerShell `install.ps1` taking a version argument. | https://docs.veracode.com/r/Install_a_specific_version_of_the_CLI | docs only (read 2026-11-12) |
| No official Veracode CLI Docker image on Docker Hub (`veracode/veracode-cli` not found). | https://hub.docker.com/v2/repositories/veracode/ | observed (2026-11-12) |
| Self-computed SHA-256 of the pinned tarball, recorded by us | - | verified locally 2026-11-12 (section 8) |

## 5. SCA agent in CI

| Fact | Source | Marker |
|---|---|---|
| Documented GitLab step: add `curl -sSL https://sca-downloads.veracode.com/ci.sh \| sh` (docs place it in `after_script`); token in masked CI variable `SRCCLR_API_TOKEN`. Agent type is created as "Bitbucket Pipelines" in the Platform; GitLab mirrors that flow. | https://docs.veracode.com/r/Integrate_agents_with_GitLab | docs only (read 2026-11-12) |
| `https://download.sourceclear.com/ci.sh` and `https://sca-downloads.veracode.com/ci.sh` are byte-identical (same SHA-256 on fetch; Last-Modified 2024-12-17). Current docs use the veracode.com host. | both URLs | observed (2026-11-12) |
| ci.sh downloads `https://sca-downloads.veracode.com/srcclr-<version>-<os>.tgz` where os is `linux`, `linux_musl_x64` (Alpine) or `macosx`; x86_64 only on Linux. Version comes from `https://sca-downloads.veracode.com/LATEST_VERSION` unless overridden. | https://sca-downloads.veracode.com/ci.sh | docs only (read 2026-11-12) |
| ci.sh honours env var `SRCCLR_VERSION` to pin the agent version. This variable is in the script but **not in the docs** pages read. | script; https://docs.veracode.com/r/Integrate_SCA_agents | docs only (read 2026-11-12) |
| Other env vars (documented): `DEBUG`, `NOCACHE`, `CACHE_DIR` (default `/tmp`), `NOSCAN`, `SCAN_DIR`, `SRCCLR_CI_JSON`, `VERBOSE`, `CUSTOM_JRE_DIR`. Custom agent commands: `... \| sh -s -- scan ...`. Default command: `scan --allow-dirty`. | https://docs.veracode.com/r/Integrate_SCA_agents | docs only (read 2026-11-12) |
| ci.sh performs **no checksum or signature verification** of the tgz; it extracts and `exec`s `srcclr`. If `LATEST_VERSION` cannot be fetched it falls back to version "latest". | script | docs only (read 2026-11-12) |
| Latest agent version: **3.8.125** (`LATEST_VERSION`). Versioned tgz reachable: `srcclr-3.8.125-linux.tgz` (200), `srcclr-3.8.100-linux.tgz` (200), `srcclr-latest-linux.tgz` (200). | https://sca-downloads.veracode.com/LATEST_VERSION | observed (2026-11-12) |
| A detached PGP signature exists: `srcclr-3.8.125-linux.tgz.asc` (200). `.sha256` and `.sig` return 403. Which public key verifies it is **not confirmed**; the yum repo config in docs references `https://sca-downloads.veracode.com/redhat/SRCCLR-GPG-KEY`. | https://sca-downloads.veracode.com/srcclr-3.8.125-linux.tgz.asc ; https://docs.veracode.com/r/Set_up_SCA_agents | observed (2026-11-12) |
| Package-manager installs (apt-get, yum with `gpgcheck=1`, Homebrew, PowerShell `ci.ps1`) are documented as alternatives. | https://docs.veracode.com/r/Set_up_SCA_agents | docs only (read 2026-11-12) |
| Official SCA agent Docker image: none in the `veracode` Docker Hub namespace; none found in docs. | https://hub.docker.com/v2/repositories/veracode/ | not confirmed (none found) |
| `gpg --verify` of the .asc against the vendor key; `SRCCLR_VERSION` pin behaviour | - | verified locally 2026-11-12: signature good (section 8); `SRCCLR_VERSION` not exercised (the component does not run ci.sh) |

## 6. Direct downloads: pipeline-scan zip and Java API wrapper

| Fact | Source | Marker |
|---|---|---|
| `pipeline-scan-LATEST.zip` reachable; Last-Modified 2026-11-10, 7,880,891 bytes (same size as the 26.11.0 zip). | https://downloads.veracode.com/securityscan/pipeline-scan-LATEST.zip | observed (2026-11-12) |
| Versioned zips exist (HTTP 200): `pipeline-scan-26.11.0.zip`, `-26.9.0.zip`, `-26.7.0.zip`, `-25.8.2.zip`, `-22.9.0.zip`. The pattern is not documented; docs only reference LATEST and recommend the Docker image. | https://downloads.veracode.com/securityscan/pipeline-scan-26.11.0.zip | observed (2026-11-12) |
| No checksum file found (`pipeline-scan-LATEST.zip.sha256` returns 404). | same host | observed (2026-11-12) |
| Docs recommend fetching LATEST on every run or caching it; this conflicts with version pinning, so pinning is our decision, not vendor guidance. | https://docs.veracode.com/r/Pipeline_Scan | docs only (read 2026-11-12) |
| Java API wrapper on Maven Central `com.veracode.vosp.api.wrappers:vosp-api-wrappers-java`: latest and release = **26.10.20.1**; previous: 26.10.20.0, 26.3.19.0, 26.2.18.0, 25.11.17.0, 25.8.16.1. Maven Central serves `.sha1`/`.md5` (and normally `.asc`) per artifact. | https://repo1.maven.org/maven2/com/veracode/vosp/api/wrappers/vosp-api-wrappers-java/maven-metadata.xml | observed (2026-11-12) |
| Docker tags 26.3.19.0.1 / .0.2 exist for the wrapper image without a matching Maven version (image rebuilds). | Docker Hub API vs Maven metadata | observed (2026-11-12) |
| Jar inside the zip matches the Docker image version; zip SHA-256 recorded by us | - | not verified locally (the component uses the Docker image, not the zip) |

## What this means for the pack

Preference ladder, highest first.

1. **Vendor-maintained integration (GitLab Workflow Integration).** Document as the vendor option; do not build it. It fits only if the organisation is on GitLab.com Premium/Ultimate, accepts a group-wide PAT with `api` scope held by Veracode, accepts webhooks plus a `veracode` project per group, and can live with auto-packaging and the fixed language matrix. Gating there is `veracode.yml` (`policy`, `break_build_policy_findings`), not jar flags. Self-managed support is contradictory in the docs: confirm with Veracode before recommending.
2. **Organisation-owned shared component (the direction of the pack).** Our own CI/CD component, pinned by consumers at a released version or SHA. The Veracode catalog components under `gitlab.com/veracode/veracode-components` are useful as a reference for input naming (`veracode_policy_name`, `policy_file`, `baseline_file`, `app_id`, `development_stage`) but are 0.0.x, catalog-unverified, absent from docs.veracode.com, and clone their own repo at job time. Do not depend on them directly until support status is confirmed; if used, pin by SHA.
3. **Pinned CLI/wrapper in script steps (what the component runs inside).**
   - SAST gate: `veracode/pipeline-scan` pinned by `tag@sha256:digest` (digests in section 3). Use `--policy_name` for built-in policies; for custom policies run `--request_policy` then `--policy_file`; add `--baseline_file` so only new policy-violating flaws fail. Treat exit 1-200 as "findings" and 253-255 as "scan error" so the two can be handled differently.
   - Platform scans: `veracode/api-wrapper-java` pinned by digest, or the Maven Central jar at a fixed version with checksum.
   - Veracode CLI: pin with `VERACODE_CLI_VERSION`; no vendor checksum exists and old versions disappear, so mirror the tarball internally (`VERACODE_CLI_DOWNLOAD_URL`) and record our own SHA-256. CLI gate exit code is 3, not a flaw count.
   - SCA agent: pin with `SRCCLR_VERSION` (script-only, undocumented) or download the versioned tgz directly and verify the `.asc`; avoid unpinned `curl | sh` in the shared component.
4. **Raw API, agent-side only.** Keep for the onboarding agent (profile lookup, policy listing, results retrieval), never as the pipeline gate. Not researched further here.

Open items to verify locally: plain vs `cmd-` image variants; `--policy_file` combined with `--fail_on_severity`; PGP key for the SCA tgz signature.


## 8. Verified locally on 2026-11-12 (demo host, x86_64; local GitLab CE 19.5.4, runner 19.5 docker executor)

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
