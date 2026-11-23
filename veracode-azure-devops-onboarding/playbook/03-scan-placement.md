# 03 Scan placement by branching model

Principles, then the table. Each scan type has one job: put it where its result is useful and
nowhere else.

- **Pipeline Scan** (minutes, results in the job): where a developer is waiting — short-lived
  branches and merge requests. Criteria: the **Veracode policy assigned to the application
  profile**. How hard it gates: the **rollout stage** (playbook/00); in `block-new` it fails on
  flaws that violate the policy and are **not in the baseline of the branch the MR targets**.
- **Baseline**: an unfiltered Pipeline Scan of each long-lived branch that MRs target, published
  per branch (GitLab: generic package `veracode-baseline/<branch slug>`) for the MR job to fetch.
- **Policy scan** (Upload and Scan without a sandbox): only at the release point. It sets the
  compliance verdict and only one may be open per profile.
- **Sandbox scan**: one sandbox per long-lived branch whose code waits before it reaches the
  release point: an integration branch that is promoted by merge (develop, or `main` when a
  `production` branch releases) and each release/x.y line. A trunk that is tagged directly gets
  no sandbox: its baseline plus the policy scan on the tag cover it. Pre-release tags
  (`-rc.N`, `-beta.N`) share one sandbox `prerelease`; they never get a policy scan. Never one
  sandbox per feature branch (the per-application sandbox count is limited and the results flip
  with whichever scanned last).
- **Deploy/environment branches** that only receive merges (`staging`, `production`): no gated
  Pipeline Scan and no baseline there (`gate_skip_branches`); the one that ships gets the policy scan.
- **Stale and decoy refs** (no commits for months, superseded model, tags that never deployed):
  nothing. Say so in the plan and suggest deleting them.
- **Agent-based SCA**: cheap and read-only; run it on every branch pipeline. It reports to the
  SCA workspace, not to the application profile. (The policy scan runs its own SCA on the
  uploaded package, and that one does count in the verdict: reference/platform-facts.md.)
- **Container scan**: on the refs where the team's own pipeline builds the image, no others.
  On MRs it is where the base image can still be changed; on the release point it is the record.
  If the Dockerfile copies build output, the scan job needs that job's artifacts
  (`container_needs`) or the pushed image (`container_image`).
- **Application profiles**: one per deployable that is released on its own (monorepo: one per
  app, one include of the shared unit per app). Parallel supported release lines (1.x and 2.x
  both get patches): one profile per line, otherwise a patch of the old line overwrites the
  verdict of the current one. Raise the count as a question; profiles cost licences in some contracts.
- **Language without Veracode Static support**: check `reference/platform-facts.md` and the
  supported-languages page; if the language is on neither the Static nor the Pipeline Scan list,
  say so plainly, set `static_scan: false`, and keep SCA (if the package manager is supported),
  the directory scan and the container scan. Do not invent a package.
- **Scan names**: policy and sandbox scans are found later by name. `Release <tag>` at the
  release point, `<branch> <short sha>` elsewhere.

| Model | Short-lived branches / MRs | Long-lived non-release branches | Release point |
|---|---|---|---|
| **GitHub flow** (feature -> main, main deploys) | Pipeline Scan vs main baseline, SCA, container | — | **main**: baseline, policy scan `main <sha>`, SCA, container |
| **git-flow** (feature -> develop; release/x.y -> main + tag; hotfix from main) | feature/bugfix: Pipeline Scan vs develop baseline, SCA. hotfix: Pipeline Scan vs main baseline, SCA | develop: baseline, sandbox `develop`, SCA. release/*: Pipeline Scan vs develop baseline, sandbox `release-x-y`, SCA, container | **tag vX.Y.Z**: policy scan `Release vX.Y.Z`. main: baseline, SCA, container |
| **Trunk + tags** (fix/* -> main; tags release) | Pipeline Scan vs main baseline, SCA | main: baseline, SCA (no sandbox). Pre-release tags: sandbox `prerelease` | **final tag vX.Y.Z**: policy scan `Release vX.Y.Z`, container |
| **Environment branches** (main -> staging -> production by merge) | Pipeline Scan vs main baseline, SCA | main: baseline, sandbox `main`, SCA. staging: nothing gated | **production**: policy scan |
| **Release branches** (release/x.y are long-lived, hotfixes land there) | Pipeline Scan vs the target release branch's baseline, SCA | each release/x.y: baseline, sandbox per line, SCA | the branch (or tag) that ships: policy scan |
| **Monorepo** | as above per child, with `rules:changes` on the child's path and one application profile per deployable | | |

Worked files: `templates/gitlab/examples/` (GitHub-flow Python, git-flow Java, trunk+tags Node).

## From the table to the shared unit's inputs (GitLab component)

Placement is not written as jobs in the repository; it is expressed as inputs of the include.
An unset regex input is `'^$'` (never).

| Model | Inputs that differ from the defaults |
|---|---|
| GitHub flow | none (`baseline_branches: '^main$'`, `release_branches: '^main$'` are the defaults) |
| git-flow | `baseline_branches: '^(main|develop)$'`, `baseline_map: 'hotfix/*=main,*=develop'`, `sandbox_branches: '^(develop|release\/.*)$'`, `release_branches: '^$'`, `release_tags: '^v'`, `container_branches: '^(main|release\/.*)$'` |
| Trunk + tags | `release_branches: '^$'`, `release_tags: '^v\d+\.\d+\.\d+$'` (anchored: `'^v'` would also match `v1.2.0-rc.1`), `sandbox_tags: '^v.*-(rc|beta)'` if pre-release tags exist, `container_branches: '^$'`, `container_tags` = the release tags |
| Environment branches (main -> staging -> production) | `baseline_branches: '^main$'`, `sandbox_branches: '^main$'`, `gate_skip_branches: '^(staging|production)$'`, `release_branches: '^production$'` |
| Monorepo | one include per application: `job_suffix: '-<app>'`, `app_name`, `package_job`, `artifact`, `source_dir: apps/<app>`, `changes_paths: ['apps/<app>/**/*', 'libs/**/*']`, `dockerfile`, and `release_tags: '^<app>\/v'` when tags are per app |
| Unsupported language | `static_scan: false` |
| Release branches | `baseline_branches: '^release\/.*$'`, `sandbox_branches: '^release\/.*$'`, `release_branches`/`release_tags` = whatever ships |

Every model also sets `app_name`, `sca_image` (the project's build image), `stage` (an existing
stage at or after the packaging job's) and `rollout_stage`.

## Gate wording for the plan

- "Rollout stage `<stage>`. Criteria: Veracode policy `<name>` of application `<profile>`
  (read at run time). MRs to `<target>` are compared with the `<target>` baseline; until the
  first baseline exists the job reports and does not fail."
- "Policy scan on `<release point>` waits up to N minutes for the verdict. In `block-policy` the
  job fails if the application does not pass; in the earlier stages the verdict is reported
  (warning) and the pipeline continues."
- If a severity override is used: "Override: gate on `<severities>` instead of the policy,
  because `<reason>`; approved by `<who>`."

## Fork merge requests

Jobs that use the credentials must not run for MRs from forks (rule 7): `rules` on
`$CI_PIPELINE_SOURCE == "merge_request_event" && $CI_MERGE_REQUEST_SOURCE_PROJECT_ID != $CI_PROJECT_ID`
→ `when: never`, placed first. The examples use branch pipelines, where fork pipelines run in
the fork's own project without the group variables.
