# Evidence register: ONB

| ID | Basis | Checked | Source or observation | Claim as written in the skill | File |
|---|---|---|---|---|---|
| ONB-01 | source | 2026-10-09 | git ls-remote | For customers not using repository scanning (Bitbucket, GitHub Enterprise Server, US Federal, Jenkins and other CI), or who want per-pipeline control. Action tags ; inputs read from each action's `action.yml`. | `veracode-onboarding/reference/ci-pipelines.md` |
| ONB-02 | lab | 2026-11-12 | observed against a live tenant | Pipeline Scan accepts 6 submissions per minute per API user; more return HTTP 429. A handful of parallel pipelines on one service account reach that, so retry on 429 or give busy groups their own service account . | `veracode-onboarding/reference/ci-pipelines.md` |
| ONB-03 | docs | 2026-10-09 | docs.veracode.com: Install the Veracode CLI, veracode package, veracode static scan, veracode scan, Run Container Security scans, About auto packaging, c_comp_quickref, SCA agent-based scan quickstart | The fastest way to see real results on one application, and the tool most automation is built from. Sources . | `veracode-onboarding/reference/cli-and-packaging.md` |
| ONB-04 | lab | 2026-11-12 | observed against a live tenant | Seen in lab testing : `veracode package` exited 0 with no | `veracode-onboarding/reference/cli-and-packaging.md` |
| ONB-05 | lab | 2026-11-12 | observed against a live tenant | `veracode package` exits 0 but there is no artifact, or a small one | `veracode-onboarding/reference/cli-and-packaging.md` |
| ONB-06 | lab | 2026-11-12 | observed against a live tenant | Scan says success, zero findings, on a language that is not supported (for example Rust) | `veracode-onboarding/reference/cli-and-packaging.md` |
| ONB-07 | docs | 2026-10-09 | docs.veracode.com | — confirm role names against the customer's | `veracode-onboarding/reference/platform-setup.md` |
| ONB-08 | docs | 2026-10-09 | docs.veracode.com/r/t_create_users | ### Create one in the Platform | `veracode-onboarding/reference/platform-setup.md` |
| ONB-09 | docs | 2026-10-09 | docs.veracode.com/r/c_API_roles_details | ### API roles by job | `veracode-onboarding/reference/platform-setup.md` |
| ONB-10 | docs | 2026-10-09 | docs.veracode.com/r/REST_APIs_Quickstart | ### Generate HMAC credentials in the Platform | `veracode-onboarding/reference/platform-setup.md` |
| ONB-11 | docs | 2026-10-09 | docs.veracode.com/r/HMAC_credentials | ### Lifecycle — put these on a calendar | `veracode-onboarding/reference/platform-setup.md` |
| ONB-12 | docs | 2026-10-09 | docs.veracode.com/r/Static_Analysis_Quickstart | ### Create one in the UI | `veracode-onboarding/reference/platform-setup.md` |
| ONB-13 | dated | 2026-10-09 | source not recorded | One installation scans many repositories from a central configuration, without editing each repo's pipeline. Veracode calls these the Workflow Integrations (or Repository Scanning). Sources: `docs.veracode.com/r/SCM_integrations` and the per-platform pages ; the GitHub template and config read | `veracode-onboarding/reference/repo-scanning.md` |
| ONB-14 | dated | 2026-10-09 | source not recorded | One installation scans many repositories from a central configuration, without editing each repo's pipeline. Veracode calls these the Workflow Integrations (or Repository Scanning). Sources: `docs.veracode.com/r/SCM_integrations` and the per-platform pages [ONB-13~]; the GitHub template and config read from `github.com/veracode/github-actions-integration` . | `veracode-onboarding/reference/repo-scanning.md` |
