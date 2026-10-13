# Repository scanning — the GitHub, GitLab and Azure DevOps workflow integrations

One installation scans many repositories from a central configuration, without
editing each repo's pipeline. Veracode calls these the **Workflow Integrations**
(or **Repository Scanning**). Sources: `docs.veracode.com/r/SCM_integrations` and
the per-platform pages `[v: 2026-10-09]`; the GitHub template and config read
from `github.com/veracode/github-actions-integration` `[v: 2026-10-09]`.

---

## 1. Is it available to them?

| Platform | Workflow integration | Notes |
|---|---|---|
| GitHub.com, GitHub Enterprise Cloud | **Yes** | `github.com` domains only |
| GitHub Enterprise Server | **No** | Use CI pipelines (`ci-pipelines.md`) |
| GitLab.com | **Yes** | Premium and Ultimate only; not GitLab Dedicated |
| GitLab self-managed | **Yes** — separate install | Linux runners; allowlist Veracode URLs and IPs |
| Azure DevOps (cloud) | **Yes** | Git repos in ADO |
| Bitbucket | **No** | SCA agent only; use CI pipelines for SAST |
| US Federal (FedRAMP) region | **No** | On any platform |

What each scans (subject to licences): **SAST** via Pipeline Scan, **SCA** via the
agent, **IaC and secrets**, and **Container Security**. Optional: policy and
sandbox scans that reach the Platform (below).

Language support for SAST includes .NET, Android, Go, Java, JavaScript, Kotlin,
Python, React Native, Ruby, Scala and TypeScript — **not PHP**. Repos are built
automatically by default; apps with unusual builds need a custom build step.

## 2. Prerequisites

| | GitHub | Azure DevOps | GitLab |
|---|---|---|---|
| Veracode role | Administrator or Security Lead | Administrator or Security Lead | Administrator or Security Lead |
| SCM role | Organization owner (or admin rights to install apps) | Organization owner | Owner of the target groups |
| Token | Org-owner PAT. Classic needs `repo`, `workflow`, `read:org` | **Installation PAT**: Code (Read, Write & Manage), Extensions (Read & Manage), Project and Team (Read, Write & Manage). **Configuration PAT**: Build (Read & Execute), Code (Read & Write), Work Items (Read & Write) | PAT with the `api` scope, from a user (ideally a service user) with access to every target group |
| Veracode credentials | **HMAC** API ID + key of an API service account | same | same |
| SCA | An SCA **agent token** for agent-based SCA (optional) | same (`SRCCLR API TOKEN`, optional) | same |

Use a dedicated **API service account** for the Veracode credentials
(`platform-setup.md` §3) — if a person's keys are used, scanning stops when they
leave. PATs from an individual have the same problem; prefer a service user in
the SCM where the platform allows it.

## 3. Install

All three can be started in the Veracode Platform: **Repository Scan** in the
left menu, then the platform.

### GitHub

1. Import `https://github.com/veracode/github-actions-integration.git` into the
   organization as a **private** repository named **`veracode`** — import, don't
   fork (a fork is public).
2. Organization Settings → Actions → General: allow the Veracode actions the
   workflows use (for example `veracode/veracode-sca@*`,
   `veracode/Veracode-pipeline-scan-action@*`).
3. Install the **Veracode Workflow App** (GitHub Marketplace) on all repositories,
   or on selected ones — which must include `veracode`.
4. Organization secrets, granted to the `veracode` repo: `VERACODE_API_ID`,
   `VERACODE_API_KEY` (HMAC), and `VERACODE_AGENT_TOKEN` for SCA. Alternatively,
   enter the credentials through **Repository Scan** in the Platform.
5. EU-hosted SCA: set `SRCCLR_REGION: ER` in `.github/workflows/veracode-sca-scan.yml`.

### Azure DevOps

**Repository Scan** → **Azure** → **Next** → ORGANIZATION, INSTALLATION PAT,
CONFIGURATION PAT → accept → VERACODE API ID, VERACODE API KEY (SRCCLR API TOKEN
optional) → **Install**. Creates a **`veracode`** project and webhooks on existing
projects; webhooks for new projects follow within about six hours (or re-run the
install). Change credentials later with **Update Installation**.

### GitLab.com / self-managed

**Repository Scan** → **GitLab** (or **GitLab Self-Managed**, which also asks for
the hostname) → PAT → choose groups → VERACODE API ID and KEY (SRCCLR API TOKEN
optional) → **Install**. Creates a **`veracode`** project in each selected group
and group webhooks. Self-managed: set `default:runs_on` to your runner name.

**It worked when** a push to a test repository starts a Veracode workflow or
pipeline in the `veracode` repo/project and a check appears on the commit or pull
request.

## 4. Configure — `veracode.yml` and `repo_list.yml`

Both live in the central `veracode` repo/project. A `veracode.yml` in an
individual repository's root overrides the central one for that repo.

**`repo_list.yml`** — which repositories are scanned. Quote every pattern:

```yaml
include_repos:
  - 'payments-*'        # start with a pilot, not '*'
exclude_repos:
  - 'veracode'
```

**`veracode.yml`** — one section per scan type: `veracode_static_scan`,
`veracode_sca_scan`, `veracode_iac_secrets_scan`. The settings that decide how
the rollout feels (defaults from the template):

| Key | Default | Decide |
|---|---|---|
| `push.trigger` / `pull_request.trigger` | `true` / `true` | Which events scan. `branches_to_run` (or `branches_to_exclude`), PR `action` (`opened`, `synchronize`) and `target_branch` |
| `analysis_on_platform` (static) | **`false`** | **Results reach the Platform only when `true`.** Then the default branch's scans become policy scans in a profile named after the repo, and compliance and reporting work. Leave `false` and the Platform shows nothing |
| `break_build_policy_findings` | **`true`** | Fails the check when findings violate the policy. On day one that includes the backlog |
| `break_build_on_error` | `false` static · `true` SCA and IaC | Whether a scan error fails the check |
| `break_build_invalid_policy` | `true` | Fails when the policy name does not exist |
| `policy` | `'Veracode Recommended Medium + SCA'` | Used when a profile has no policy yet |
| `create_code_scanning_alert` | `false` | GitHub Security tab alerts for static findings |
| `create_issue` | `false` | GitHub Issues for static findings (`create_work_items` on Azure DevOps) |
| `issues.trigger` / `commands` | `false` / `"Veracode Static Scan"` etc. | On-demand scans from an issue or comment |

Azure DevOps adds `pool_name` (default `Azure Pipelines`); GitLab adds
`filter_mitigated_flaws` (default `true`). Builds: `use_custom_workflow`,
`runs_on`, `packager_image`, and a pre-dependency command for apps the automatic
build cannot handle.

## 5. A rollout that survives week one

1. **Pilot.** `include_repos` lists two or three repos in the main languages.
   Check each one's packaging (the scan log shows the modules found) before
   widening.
2. **Agree the break-build stance first.** With the default
   `break_build_policy_findings: true`, every PR against a repo with old findings
   fails. Options: start with `false` while teams triage, or keep `true` on a few
   repos whose owners agreed. Write down when it flips.
3. **Turn on `analysis_on_platform`** once profile names are agreed
   (`platform-setup.md` §6), so compliance and reporting see the results.
4. **Widen `include_repos`** in batches; track coverage (CSM milestone M5).
5. **Tell developers where results appear** — checks on the PR, the Security tab
   or issues if enabled — before the first red check arrives.

## 6. Where results appear

- **On the commit or PR:** status checks (GitHub Checks tab or inline in Files
  changed; Azure DevOps **Veracode Scans** tab on the pipeline; GitLab pipeline log
  in the `veracode` project, artifacts in `veracode-artifact`).
- **GitHub Security tab / Issues / ADO Work Items:** only if enabled.
- **Veracode Platform:** only with `analysis_on_platform: true` — profiles named
  `{organization}/{repository}`, `ADO/{organization}/{project}/{repository}` or
  `GITLAB/{group}/{repository}`.
- **Fix for SCA** can comment on PRs and open fix PRs (needs that licence).

---

## Where it goes wrong

| Symptom | Usual cause |
|---|---|
| Nothing in the Platform | `analysis_on_platform` is `false` (the default) |
| Every PR fails from day one | `break_build_policy_findings: true` meeting the existing backlog |
| A repo never scans | Not in `include_repos`, in `exclude_repos`, Workflow App not installed on it, or patterns not quoted |
| Workflows blocked from starting (GitHub) | Organization Actions policy does not allow the Veracode actions |
| SAST skipped for a repo | Unsupported language (PHP) or the automatic build failed — use a custom build step |
| Scans fail for one repo only | Non-standard characters (emoji, non-English) in its name or description |
| Self-hosted or self-managed runners time out | Veracode URLs/IPs not allowlisted; Linux runners also need `wget` |
| Scanning stops after someone leaves | The PAT or Veracode keys belonged to a person |
| US Federal customer cannot find it | Not available in that region — use CI pipelines |
