# VeracodeAISkills

Agent skills for working with Veracode, for Claude and other tools that load
`SKILL.md` skills.

| Skill | Use it for |
|---|---|
| [`veracode-integration`](veracode-integration/) | Building against the Veracode APIs: findings exports and BI feeds (Power BI, Fabric), Jira/ServiceNow sync, mitigations, CI/CD wiring, users and credentials, HMAC signing and the legacy XML APIs (build- and scan-name-scoped results), Reporting and Custom PDF APIs, troubleshooting API errors |
| [`veracode-onboarding`](veracode-onboarding/) | Getting started: platform setup, API service accounts and credentials, repository scanning (GitHub, GitLab, Azure DevOps workflow integrations), the Veracode CLI and packaging, CI pipeline gates. Also a CSM mode for kickoffs, readiness questionnaires, plans, trackers and status updates |
| [`veracode-repo-onboarding`](veracode-repo-onboarding/) | An agent adding Veracode to one repository's existing CI: find the branching model, place Pipeline, sandbox and policy scans, prove the package, open one additions-only merge request that includes a shared GitLab component, verify the results. GitLab CI syntax; the playbooks are SCM-neutral |
| [`veracode-azure-devops-onboarding`](veracode-azure-devops-onboarding/) | The Azure DevOps twin of the previous skill: an agent adding Veracode to one repository's Azure Pipelines through `tools/ado.py`: discover branches, tags, branch policies and pipelines, use the organisation's `veracode-pipelines` template repository pinned by tag (or a copy, or the marketplace task for upload only), lint with the preview API, open one pull request per long-lived branch, verify the run. `audit` stage only; one repository tested |
| [`veracode-packaging-proof`](veracode-packaging-proof/) | Choosing the artifact for static analysis and proving it is the right one by comparing candidate scans; diagnosing a scan that came back green with few or no findings |
| [`veracode-gitlab-component`](veracode-gitlab-component/) | One shared, versioned Veracode GitLab CI/CD component (1.3.1 included) that repositories include by reference: setting it up, writing the include, moving from audit to block, releasing it |

Each skill folder holds a `SKILL.md` (the router and rules) and a `reference/`
folder that the skill reads on demand. The ones added in 2026-11 also carry
playbooks, templates and small helper scripts.

`veracode-onboarding` is the getting-started and CSM guide for people.
`veracode-repo-onboarding` (GitLab) and `veracode-azure-devops-onboarding` (Azure DevOps)
are the step-by-step playbooks an agent follows to change one repository.

## Install

- **Claude apps:** install the `.skill` file for each skill you want (attached to
  the release, or build it as below). Each skill installs separately.
- **Claude Code:** copy a skill folder into `~/.claude/skills/` (personal) or
  `.claude/skills/` in a repository (project).

To build a `.skill` file yourself, zip the skill folder itself, so the archive
contains `<skill-name>/SKILL.md` and `<skill-name>/reference/…`, and rename the
`.zip` to `.skill`:

```bash
zip -r veracode-integration.skill veracode-integration
zip -r veracode-onboarding.skill veracode-onboarding
zip -r veracode-repo-onboarding.skill veracode-repo-onboarding
zip -r veracode-azure-devops-onboarding.skill veracode-azure-devops-onboarding
zip -r veracode-packaging-proof.skill veracode-packaging-proof
zip -r veracode-gitlab-component.skill veracode-gitlab-component
```

## Shared files

The 2026-11 skills use some of the same playbooks, reference files, templates
and scripts. A skill is installed one folder at a time, so each carries its own
copy. The source for those copies is `shared/`; `shared/manifest.txt` lists which
skill gets which file.

```bash
python3 tools/sync_shared.py sync     # after editing anything under shared/
python3 tools/sync_shared.py check    # fails if a copy differs or a skill points at a file it lacks
```

Edit `shared/`, never the copies. `shared/` and `tools/` are not skills and are not
installed.

## Evidence

Skill files hold rules and short evidence IDs such as `[PS-04]`. Dates, sources and
observations are in [`evidence/`](evidence/README.md), outside the skills, so they
can be audited without loading them into an assistant. `[ID~]` means read, not run;
`[ID?]` means carried over and not re-verified. Check the two against each other with:

```bash
python3 tools/evidence.py check
```

## Tests

```bash
tests/static/run.sh
```

runs in seconds with no credentials: shared-file drift, evidence cross-check, skill
front matter, dead paths, script syntax, the scripts' own unit tests, and the rules
that must not disappear from the instructions (`tests/static/required-rules.tsv`).
Agent-behaviour scenarios (skill routing, placement, packaging, a full onboarding)
are described in [`tests/README.md`](tests/README.md); they need a lab.

## How the 2026-11 skills were tested

See [`evidence/lab-runs.md`](evidence/lab-runs.md). Component tag 1.3.0 does not
parse; use 1.3.1.


## Azure DevOps

`veracode-azure-devops-onboarding` carries the Azure facts in `reference/facts/azure-devops.md` (register `evidence/register/ADO.md`), the `tools/ado.py` that makes every Azure DevOps call, and the template repository content in `templates/azure/`. What ran: one TypeScript repository on a cloud organisation with one self-hosted agent, `audit` stage (see the facts file and `evidence/lab-runs.md`). Not tested: stages beyond `audit`, pull-request build validation, container scan, gating by baseline, Microsoft-hosted agents. A static test is `tests/static/test_azure.py`; tests that need an organisation are in `tests/azure/`.
