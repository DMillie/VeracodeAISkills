# VeracodeAISkills

Agent skills for working with Veracode, for Claude and other tools that load
`SKILL.md` skills.

| Skill | Use it for |
|---|---|
| [`veracode-integration`](veracode-integration/) | Building against the Veracode APIs: findings exports and BI feeds (Power BI, Fabric), Jira/ServiceNow sync, mitigations, CI/CD wiring, users and credentials, HMAC signing and the legacy XML APIs (build- and scan-name-scoped results), Reporting and Custom PDF APIs, troubleshooting API errors |
| [`veracode-onboarding`](veracode-onboarding/) | Getting started: platform setup, API service accounts and credentials, repository scanning (GitHub, GitLab, Azure DevOps workflow integrations), the Veracode CLI and packaging, CI pipeline gates. Also a CSM mode for kickoffs, readiness questionnaires, plans, trackers and status updates |

Each skill folder holds a `SKILL.md` (the router and rules) and a `reference/`
folder that the skill reads on demand.

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
```

## Provenance

Facts in the reference files carry `[v: date | source]` tags. `live` means the
behaviour was observed against a real Veracode tenant; anything else names the
documentation, spec or library source it was read from. Items marked
*unverified* are deliberately not asserted — the skills tell the model to check
the named source instead of guessing. Re-verify anything older than about six
months.
