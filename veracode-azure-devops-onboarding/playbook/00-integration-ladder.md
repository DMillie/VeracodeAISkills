# 00 Integration ladder, rollout stages, re-runs

SCM-neutral. Decide this before anything is written into a repository, and write the decision
into the plan ("Integration rung: N, because …"). Sources and dates for the vendor facts:
`reference/integration-options.md`.

## The preference ladder

Take the highest rung that works for this organisation and this SCM. Going lower needs a reason
in the plan; "it was quicker" is not one.

| Rung | What | Use when | Who maintains it |
|---|---|---|---|
| 1 | **Vendor-maintained integration for the SCM** (GitLab: Veracode GitLab Workflow Integration / repository scanning; GitHub: Veracode Workflow app; Azure DevOps: the Veracode extension tasks) | the organisation's SCM edition, hosting and tier are supported, the security team owns the installation, and its fixed behaviour (auto-packaging, where scans run, how results appear) fits | Veracode |
| 2 | **One organisation-owned shared unit**: a CI/CD component, shared template, reusable workflow or task group in ONE central project, released with semantic versions, included **by reference, pinned to a release** | rung 1 is not available or not adopted. This is the default for self-managed SCMs and for teams that need placement by branching model | the platform/security team |
| 3 | **Pinned Veracode CLI / official wrapper in script steps** (inside the shared unit, or directly in the repository only as a stop-gap) | a scan type the shared unit does not cover yet | whoever wrote the step: record it and propose it for the shared unit |
| 4 | **Raw Veracode API calls** | only agent-side setup (application profile, reading a verdict), only in the call styles of this pack's `tools/` scripts and the official API wrapper; **never inside a customer pipeline** | the onboarding agent |

Rules that hold on every rung:

- **By reference, not by copy.** A repository carries an include and its inputs, not job
  definitions. A per-repository copy of the shared unit is the documented last resort (the
  project cannot read the central project and that cannot be fixed) and the plan must say why.
- **Pinned.** Exact release of the shared unit (never a branch, never "latest"); inside it,
  images by tag and digest, tools by version with a checksum or signature check; no remote
  install script piped into a shell. One place to bump: the shared unit's input defaults.
- **Never fork the shared unit into the repository to change it.** Missing capability → a
  change request to its owners (new input with a default, minor release).
- **Credentials by name.** The shared unit reads the same variable names everywhere.

## Discovery comes first: is there already a shared unit?

Before choosing, look (playbook/02 has the calls):

1. Vendor integration already installed? (GitLab: a `veracode` project created by the Workflow
   Integration in the group, webhooks on the group; the security team knows.) → rung 1; this
   pack's job is then only to check the repository is covered. Do not add CI jobs next to it.
2. An organisation component/template project? (CI/CD Catalog, a `platform`/`security`/`ci`
   group, `include:` lines in sibling repositories of the same group, instance-level required
   pipeline configuration.) → rung 2 with **that** unit and its newest release.
3. Does this repository already include it? → re-run logic below.
4. None, and the organisation wants one → create the central project from
   `templates/gitlab/component/` (a platform-team decision, made once, not per repository),
   release `1.0.0`, then onboard repositories against it.

## Rollout stage: one input

| Stage | Short-lived branches (fast scan gate) | Release point (policy scan) | Use |
|---|---|---|---|
| `audit` | never fails; findings and "would fail" count in the log; tool errors are warnings | verdict printed, never fails | first onboarding MR, first weeks |
| `warn` | policy-violating flaws → allowed failure (visible warning) | Did Not Pass → warning | teams see the gate before it bites |
| `block-new` | fails on **new** policy-violating flaws compared with the target branch's baseline; warning while no baseline exists | Did Not Pass → warning | default steady state once a baseline exists |
| `block-policy` | fails on **any** policy-violating flaw (no baseline) | job fails unless the application passes policy | regulated releases; backlog already burned down |

- Criteria are the **Veracode policy assigned to the application profile**, resolved at run
  time. Severity lists are an explicit override input, recorded in the plan with the reason.
- Changing stage is a one-line change of the include's input, reviewed like any other MR.
- Default: `audit` on the onboarding MR. In the summary, recommend `block-new` and name the
  condition (the target branch has published a baseline).
- Record the chosen stage in the plan and the summary.

## Re-running on an onboarded repository (idempotency)

Run `tools/detect_integration.py <ci-file>` (it reads the newest release from the component
project) before planning:

| Found | Action |
|---|---|
| shared unit included at the newest release | **nothing to do**: report the rung, version, rollout stage; stop |
| shared unit included at an older release | **upgrade**: a one-line version-bump MR; read the unit's changelog into the MR description |
| shared unit included at a branch / floating ref | **pin** to the newest release (one line) |
| per-repository copy (last-resort rung or the 2026-11-11 layout) | **migrate**: replace the local include and the copied file by the reference include, in one MR |
| Veracode jobs not from the shared unit (hand-written, vendor catalog component, vendor app) | **review**: report what exists; do not add a second integration |
| nothing | onboard (steps 1–6) |

Never add jobs when an integration is present; duplicated scans double the cost and a second
policy scan can delete the first one's open build.
