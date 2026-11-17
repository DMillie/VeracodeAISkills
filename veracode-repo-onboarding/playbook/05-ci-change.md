# 05 Additive CI change (GitLab)

Pre-condition: the plan (`repo-plan.md`) is approved, or its defaults were pre-approved, and it
names the integration rung (playbook/00). This playbook is rung 2: the organisation's shared
component, included by reference. On rung 1 (vendor integration installed) nothing here applies.

## Once per organisation (platform team, not per repository)

The central project (e.g. `platform/veracode-ci`) holds `templates/gitlab/component/` of this
pack: `templates/veracode/template.yml`, README, CHANGELOG, `tools/pin-versions.sh`. It is
visible to every project that must include it (internal, or the consuming groups are members),
its tags are protected and are semantic versions without a `v` prefix (`1.0.0`), and each tag has
a release. Consumers pin an exact tag. If it does not exist, stop and ask who owns it; creating
it is not part of onboarding a repository.

## Checklist per repository

1. **Detect**: `tools/detect_integration.py <ci-file>`. Continue only on `onboard`; `upgrade` /
   `pin` are a one-line MR (`--write` applies it); `nothing` ends the run; `migrate` / `review`
   go back to the plan.
2. **Branch** `veracode/onboarding-<target branch slug>` from the branch the MR targets (one branch and one MR per long-lived branch), in a working clone (never in
   a golden/sample copy). One MR per long-lived branch (rule 3) with the same change.
3. **Add to the CI file**, below the existing content, nothing else:
   - the include of the component at the newest release with its inputs
     (`component: $CI_SERVER_FQDN/<central project>/veracode@X.Y.Z`); inputs per playbook/03;
     `rollout_stage: audit` on a first onboarding. **If the file already has a top-level
     `include:`, append the entry to that list** (two `include:` keys = the second silently
     replaces the first and the team's own includes vanish).
   - the packaging job (playbook/04) with `artifacts:paths: [veracode-package.zip]`, running on
     every ref the Veracode jobs run on (branches, and release tags if tags are the release
     point) — unless the build already produces the deployable; then point `package_job` and
     `artifact` at it.
   The diff must be additions only: `git diff --numstat` shows 0 deletions; expect 15–40 added
   lines. No job definitions, no hidden jobs, no copied template file, no `workflow:` rules, no
   global `variables:`.
4. **Fallback forms** (same file, same inputs), only with the reason written in the plan:
   `include: project: <central project>, ref: X.Y.Z, file: templates/veracode/template.yml`
   where components are unavailable (GitLab < 17.0); a per-repository copy
   (`.gitlab/veracode/template.yml` + `include: local:` with inputs) only when the project
   cannot read the central project and that cannot be changed.
5. **Lint**: `tools/gitlab-ci-lint.sh <project> <ci-file>` (the server resolves the component;
   use a non-admin member token to prove the pipeline's users can read it). Fix until
   `valid=True` with no warnings. `GITLAB_LINT_REF=<branch>` adds a dry run on that ref, which
   lists the jobs that would be created there: check them against the placement table.
6. **Application profile** (agent-side, rung 4): `tools/veracode_app_profile.py ensure "<name>"
   --criticality MEDIUM --repo-url <web_url>`. Exact-name match; creates only when absent; prints
   the guid and the assigned policy. The component never creates profiles.
7. **Variables**: confirm by name that `VERACODE_API_KEY_ID`, `VERACODE_API_KEY_SECRET` and
   `SRCCLR_API_TOKEN` exist in scope and are not protected. Never create or read them.
8. **Push** and **open the merge request** with: the rung and the component release, the
   rollout stage and the recommended next stage, the placement table, the profile name and its
   policy, what runs on this MR versus after merge. `remove_source_branch: true`. Do not merge
   unless the person said so. (Creating the MR in the same second as the push can fail once;
   retry after the branch is visible.)
9. **Wait for the MR pipeline** (playbook/06).

## Changing the rollout stage later

One line: `rollout_stage: audit` → `block-new`, as its own MR, after the target branch's
baseline exists (the baseline job logged "Baseline published"). Say in the MR what will start
failing: new flaws that violate the application's policy.

## What not to do

- No copy of the component's jobs "to tweak one thing": ask for an input in the central project.
- No `@main`, `@~latest` or partial version on the include; no `latest` image; no
  `curl … | sh`. Tool versions are bumped in the component's input defaults only
  (`tools/pin-versions.sh`), released as a patch version, and reach repositories as a one-line MR.
- No `allow_failure: true` added in the repository to make red go away: the stage decides.
- No raw Veracode API call in the pipeline (rule 11); the component uses Veracode's images,
  wrapper, CLI and agent only.
