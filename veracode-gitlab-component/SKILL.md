---
name: veracode-gitlab-component
description: Set up, use, extend or release the shared Veracode GitLab CI/CD component (veracode-ci) that repositories include by reference instead of copying scan jobs. Use when a platform or security team wants one central, versioned Veracode pipeline definition in GitLab, when writing the include and inputs for a repo (monorepo, several artifacts, per-app tags, release lines, static off, container scans), when moving a rollout stage from audit to block, or when changing and releasing the component itself.
---

# The shared Veracode CI component for GitLab

One component, `veracode`, lives in one central project (for example `platform/veracode-ci`) and
is released with semantic version tags without a `v`. Repositories include it pinned to an exact
tag and pass inputs. Nobody copies scan jobs into a repository.

- `templates/gitlab/component/` is the project content: `templates/veracode/template.yml`, `README.md`,
  `CHANGELOG.md`, `tools/pin-versions.sh`. Current release: 1.3.1. Tag 1.3.0 does not parse; never
  pin it.
- `templates/gitlab/examples/` holds three worked `.gitlab-ci.yml` files: GitHub flow (Python), git-flow (Java),
  trunk with tags (Node).
- `playbook/00-integration-ladder.md` explains why a shared component comes before per-repo jobs, and the
  rollout stages.

Read `templates/gitlab/component/README.md` for the inputs, the jobs each input switches on, and the include forms.

Background, read only when needed: `reference/integration-options.md` indexes what Veracode ships
for GitLab, policy-driven gating and version pinning; `reference/facts/gitlab.md`,
`reference/facts/integration-layout.md` and `reference/facts/tools-and-images.md` hold dated
observed behaviour.

## Using it in a repository

1. Check whether the repo is already onboarded: `tools/detect_integration.py` answers onboard,
   upgrade (a one-line version bump) or nothing to do. Never onboard twice.
2. Add one entry to the existing top-level `include:` list. A second `include:` key silently
   replaces the first.
3. One include per deployable. Use `job_suffix` to keep job names apart, `source_dir` and
   `changes_paths` for monorepos, `static_scan: false` for unsupported languages, and the
   `container_*` inputs where the team builds images.
4. Start with `rollout_stage: audit`. Move to `block-new` once a baseline exists on the target
   branch; `block-policy` makes the release point follow the policy verdict.
5. Lint before pushing: `tools/gitlab-ci-lint.sh` resolves component includes against the GitLab
   instance (needs `GITLAB_URL` and `GITLAB_TOKEN` in the environment; never print them).

## Changing and releasing the component

1. Edit on a development branch in the component project and push it.
2. Lint a consumer file that includes the component `@<branch>`. An unquoted colon in an input
   description is enough to break parsing, and a broken tag cannot be fixed, only superseded.
3. Only then tag. Update `CHANGELOG.md` and bump the pins in the examples with
   `templates/gitlab/component/tools/pin-versions.sh`.
4. Nothing floats: no `latest` image, no install script piped into a shell.

## Known limits

- One artifact and one Dockerfile per include, so a repo with two deployables and a front end
  needs three includes.
- `policy_scan_timeout` defaults to 60 minutes, which equals GitLab's default job timeout. A slow
  Platform turns a release pipeline red even in `audit`. Raise the job timeout or lower the input.
- `gitlab-ci-lint.sh` fails with "Argument list too long" on a very large merged configuration.
- Pipeline Scan allows 6 submissions per minute per API user. The component retries on HTTP 429;
  many parallel pipelines on one service account will still queue.
- All four rollout stages were exercised on live branch pipelines on one repo. Not proven live: `block-policy` at the release point (job red on a Did Not Pass policy scan), and merge-request-event pipelines.
