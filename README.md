# VeracodeAISkills

Agent skills for working with Veracode, for Claude and other tools that load
`SKILL.md` skills.

| Skill | Use it for |
|---|---|
| [`veracode-integration`](veracode-integration/) | Building against the Veracode APIs: findings exports and BI feeds (Power BI, Fabric), Jira/ServiceNow sync, mitigations, CI/CD wiring, users and credentials, HMAC signing and the legacy XML APIs (build- and scan-name-scoped results), Reporting and Custom PDF APIs, troubleshooting API errors |
| [`veracode-onboarding`](veracode-onboarding/) | Getting started: platform setup, API service accounts and credentials, repository scanning (GitHub, GitLab, Azure DevOps workflow integrations), the Veracode CLI and packaging, CI pipeline gates. Also a CSM mode for kickoffs, readiness questionnaires, plans, trackers and status updates |
| [`veracode-repo-onboarding`](veracode-repo-onboarding/) | An agent adding Veracode to one repository's existing CI: find the branching model, place Pipeline, sandbox and policy scans, prove the package, open one additions-only merge request that includes a shared GitLab component, verify the results. GitLab CI syntax; the playbooks are SCM-neutral |
| [`veracode-packaging-proof`](veracode-packaging-proof/) | Choosing the artifact for static analysis and proving it is the right one by comparing candidate scans; diagnosing a scan that came back green with few or no findings |
| [`veracode-gitlab-component`](veracode-gitlab-component/) | One shared, versioned Veracode GitLab CI/CD component (1.3.1 included) that repositories include by reference: setting it up, writing the include, moving from audit to block, releasing it |

Each skill folder holds a `SKILL.md` (the router and rules) and a `reference/`
folder that the skill reads on demand. The three added in 2026-11 also carry
playbooks, templates and small helper scripts.

`veracode-onboarding` is the getting-started and CSM guide for people.
`veracode-repo-onboarding` is the step-by-step playbook an agent follows to
change one repository.

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
zip -r veracode-packaging-proof.skill veracode-packaging-proof
zip -r veracode-gitlab-component.skill veracode-gitlab-component
```

## Provenance

Facts in the reference files carry `[v: date | source]` tags. `live` means the
behaviour was observed against a real Veracode tenant; anything else names the
documentation, spec or library source it was read from. Items marked
*unverified* are deliberately not asserted — the skills tell the model to check
the named source instead of guessing. Re-verify anything older than about six
months.

## How the 2026-11 skills were tested

In a lab: a self-managed GitLab CE 19.5 with one docker runner and a Veracode
test tenant, eleven sample repositories with planted flaws and planted packaging
traps, one run per repository. Agents given only these files placed scans
correctly on 8 of 8 repositories and built an accepted package on 9 of 9
statically supported ones (Java, Kotlin, Scala, C#, Python, Go, PHP, Rails,
TypeScript). Facts in their reference files carry `[live <date>]` tags instead
of the `[v: …]` form above.

Not tested: GitHub, Azure DevOps, Bitbucket and gitlab.com pipelines; the GitLab
Workflow Integration; merge-request-event pipelines; `block-policy` at the
release point; Android. Component tag 1.3.0 does not parse; use 1.3.1.
