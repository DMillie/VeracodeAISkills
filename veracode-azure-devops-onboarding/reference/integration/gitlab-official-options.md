# 1. What Veracode officially ships for GitLab

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
| Behaviour of the component in our pipelines | - | verified locally 2026-11-12 (evidence register; lab run 3, lab run 4) |

### 1c. Official CI templates / examples

| Fact | Source | Marker |
|---|---|---|
| Docs give copy-paste `.gitlab-ci.yml` examples for pipeline-scan.jar (plain, issue generation, SAST report import, built-in policy). They download `pipeline-scan-LATEST.zip`; docs recommend switching to the Docker image "for improved stability". | https://docs.veracode.com/r/Example_code_for_GitLab | docs only (read 2026-11-12) |
| Importing findings as GitLab vulnerabilities needs Premium/Ultimate; issue generation works on any tier and needs a PAT with `api` scope in CI variable `PRIVATE_TOKEN`; `GITLAB_URL` overrides the API base for custom domains. | https://docs.veracode.com/r/Configure_Pipeline_Scan_setings | docs only (read 2026-11-12) |
| Veracode CLI GitLab example: `curl ... /veracode-cli/install \| sh` then `./veracode static scan <artifact>`; credentials via `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET`. | https://docs.veracode.com/r/veracode_cli_static_analysis_integration | docs only (read 2026-11-12) |
| No includable template project named "veracode-gitlab-ci-templates" found under the `veracode` group; other `veracode-*` GitLab groups/projects in search results are personal or demo namespaces. | https://gitlab.com/api/v4/projects?search=veracode | observed (2026-11-12) |
| `docs.veracode.com/r/GitLab` is the Risk Manager connector page, not a CI integration. | https://docs.veracode.com/r/GitLab | docs only (read 2026-11-12) |

Index and reading guide: `reference/integration-options.md`.
