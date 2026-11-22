# Azure DevOps facts that matter here

Sources: the lab run on one sample repository (2026-11-20), the lab's translation notes (2026-11-21),
two lab runs of the shared template (2026-11-21), and Microsoft's and Veracode's documentation read on
2026-11-21. `[ID]` was observed in the lab; `[ID~]` was read in documentation or code and not run.
**Not run at all:** rollout stages beyond `audit`, pull-request build validation, container scan, gating by
baseline, agent SCA, `staticScan: false`, policy scans on tags, the copied-file rung, the extension-task rung, a
monorepo with two calls, `ado.py run` and `ado.py profile`. Say so in the report.

## Concepts (two lines each)
- **Organisation > project > repository.** Two levels only. Settings, variable groups and the
  pipeline identity's reach are per project. A project is the nearest thing to a GitLab group.
- **Pipeline.** A separate object that points at a YAML file in a repository. The YAML does nothing
  until a pipeline points at it. One repository can have several (monorepo: one per component).
- **Stage > job > step.** Stages run in order; jobs of a stage run in parallel on fresh checkouts;
  steps run in order in one workspace. A step is `script:`/`bash:` or `task:`.
  A file with only `steps:` is one implicit job; with only `jobs:` it has no stages.
- **Agent and pool.** The runner. `pool: <name>` picks it. A self-hosted free-tier pool runs ONE
  job at a time, so queued runs wait. [ADO-21]
- **Variable group.** Library object with named variables, secrets write-only. A pipeline must
  name it (`variables:` with `- group: <name>`) and be allowed to use it. It can sit on a single job
  (`variables:` inside the job), which leaves the team's root `variables:` alone; a root `variables:` in
  mapping form cannot take a group without rewriting it. [ADO-26]
- **Service connection.** Stored credential for an outside system, used by tasks by name.
- **Template.** A YAML file with `parameters:` that a pipeline calls with `- template: file.yml`.
  A steps template inserts steps; a job or stage template inserts jobs or stages.
- **Pull request, branch policy, build validation.** See below.

## Triggers
- No `trigger:` key: every branch push starts a run. `trigger: none` disables CI runs. [ADO-11~]
- A CI run uses the YAML file as it is on the pushed branch. So each long-lived branch needs the
  change in its own copy of the file. [ADO-11~]
- A pull request run is NOT set in YAML for Azure Repos. It is a **build validation** branch
  policy on the target branch; the `pr:` key is for GitHub and Bitbucket Cloud, not for Azure Repos. [ADO-10~]
- If the team's `trigger:` lists only some branches, a branch run of the onboarding pipeline
  must be queued by hand; that is how the first lab run did it. [ADO-19] (`ado.py run` itself was not
  run in the later builds.)
- With no `trigger:` (the sample pipelines) every branch push, including `veracode/...`, starts a full
  run with the team's own stages. [ADO-27]
- Conditions have no regular expressions: `startsWith`, `contains`, `eq` only. Tag shapes are
  approximated. Example: `condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))`. [ADO-20]
- `Build.SourceBranch` is the full ref (`refs/heads/main`, `refs/tags/v1.2.0`).
  `Build.SourceBranchName` is the last segment only.

## Variables and secrets
- Secret variables are NOT passed to scripts. Map each one: `env:` with
  `VERACODE_API_KEY_ID: $(VERACODE_API_KEY_ID)`. Never put a secret on a command line. [ADO-04~]
- Ordinary variables reach scripts as upper-case environment variables with `.` as `_`
  (`Build.SourceBranch` is `$BUILD_SOURCEBRANCH`).
- Names this skill uses: group `veracode` with `VERACODE_API_KEY_ID`, `VERACODE_API_KEY_SECRET`,
  `SRCCLR_API_TOKEN`. `tools/ado.py discover` shows variable names only, never values.
- Declaring a group that is missing, or that the pipeline may not use, fails the run before any
  step starts. Authorization is the resource owner's decision (a person). [ADO-12~]

## Jobs: container or agent
- A job with `container: <image>` runs its steps inside that image. Needs a glibc Linux image
  with bash; Alpine images do not work as they are. Documentation says the agent must not itself
  run inside a container. [ADO-15~] The lab agent did, and container jobs still worked. [ADO-16]
- A job without `container:` runs on the agent and uses its tools (java, python3, curl, git,
  docker if installed). **The Veracode job added by this skill has no `container:`.**
- A team's top-level `container:` applies to every job without its own `container:` override.
  Steps appended to such a job run inside the team's image, which may lack java and curl.

## Artifacts
- **A self-hosted agent REUSES its workspace between runs.** `$(Pipeline.Workspace)` keeps what an earlier run left,
  so after `- download: current` the artifact folder can hold an older `payments-service-2.4.0.jar` (another
  branch's run) next to the new jar. `cp .../payments-service-*.jar x.jar` then fails ("target is not a directory"),
  the Pipeline Scan is skipped with only a warning, and the run still looks green. Empty the download folder
  first, require exactly one jar, print the listing (`examples/git-flow-java.after.yml`). [ADO-28]
- `- publish: <one path>` with `artifact: <name>` stores a pipeline artifact (no globs: collect
  files into one folder first). A later job reads it with `- download: current`. Files lose the
  executable bit. [ADO-20]
- Azure Artifacts (feeds) is the package registry. Not used here.

## Queued is not blocked
- A run that is `notStarted` or `inProgress` is normally waiting for the single agent; waits of 10 to 30 minutes
  are normal on a shared pool. Waiting is part of the job. The only reason to ask a person is a permission gate
  (a Checkpoint.Authorization record in the run's timeline that is not completed). `ado.py run-wait` says which. [ADO-29]

## Branch policies and what they mean for you
- A branch with any policy accepts no direct push and cannot be deleted; every change arrives by
  pull request. [ADO-09~] Treat "has a policy" as "protected". `ado.py pr-complete` with merge strategy
  `noFastForward` completed pull requests under the lab's "Require a merge strategy" policy; the merge
  started a run on the target branch, which is where the policy or sandbox scan ran. [ADO-27] `ado.py push` pushes only
  `veracode/...` branches; you always open a pull request.
- Build validation queues a pipeline when a pull request is created or updated and uses the
  result to allow the merge. Adding or changing a policy is a project setting; **this skill
  never changes it**. Without one, pull requests get no Veracode run until the branch run is
  queued by hand. [ADO-10~]
- **Known limit: pull requests get no scan** until a person adds a build validation policy (Branch policies >
  Build validation on each protected branch, pointing at the pipeline). With `trigger` on all branches, the push of
  the PR's source branch already produces a Pipeline Scan run that the reviewer can read. [ADO-10~] [ADO-27]
- Tags are not protected in Azure Repos (a "Create tag" permission instead). [ADO-22]

## The pipeline's identity and its fences
- A run acts as the project's build service identity (`$(System.AccessToken)`, mapped with `env:`
  if a script needs it). By default it reaches only its own project. [ADO-14]
- So the template repository `veracode-pipelines` must be in the SAME project as the pipeline
  that uses it. One in another project is "not open to the pipeline": stop and ask; rung 2 (a copy) needs a person's approval. [ADO-14]
- **Repository-resource gate.** A pipeline that references another repository
  (`resources: repositories:`) may wait at "needs permission" until a person clicks Permit once.
  The run stays queued, then shows "waiting for permission". Do not retry, do not delete the
  pipeline (that loses the permit). Tell the person which pipeline and which repository. [ADO-13]
  A repository resource in the same project is the usual case; whether a permit appears for
  `veracode-pipelines` was not observed. [ADO-23~]
- Resources (variable group, service connection, pool, repository) must be authorized for the
  pipeline. The error reads "Could not find a <resource> with name ... does not exist or has not
  been authorized for use". [ADO-12~]

## Template repository references
- `resources: repositories:` with `type: git`, `name: <repo>` (same project) or
  `<project>/<repo>`, and `ref: refs/tags/<tag>`. Use a tag, never a branch. A template is then
  called as `- template: veracode-steps.yml@<alias>`. A repository resource is not checked out
  unless a `checkout:` step names it; templates need no checkout. [ADO-23~]

## The preview API (lint)
- `tools/ado.py validate` uses the pipeline preview API: a dry run that queues nothing and
  returns the expanded YAML. [ADO-06~]
- It catches: YAML syntax, unknown template files or parameters, bad `resources`. It accepted
  the lab's onboarding file. [ADO-05]
- It does NOT catch: a missing or unauthorized variable group, a permission gate, a task that
  runs green and does nothing (below), a wrong package, or a wrong tool version. A green
  `validate` is not a green pipeline. [ADO-05]

## Veracode's Azure DevOps extension
- Documented tasks: Upload and Scan (`Veracode@3` on the docs page) and Flaw Importer. The page
  does not mention Pipeline Scan. Service connection type: Veracode Platform. [ADO-17~]
- Installed in the lab: extension version 4.0.0, task `Veracode@4`, connection `veracode`. Inputs
  that ran: `ConnectionDetailsSelection: 'Service Connection'`, `AnalysisService`,
  `veracodeAppProfile`, `version`, `filepath`, `createProfile`,
  `failBuildIfUploadAndScanBuildStepFails`, `importResults`, `failBuildOnPolicyFail`,
  `maximumWaitTime`. [ADO-18]
- **Collision, UNCONFIRMED.** In a job that also loaded variable group `veracode`, the task ended
  green and uploaded nothing (log: "Error occurred while accessing the Veracode Platform"; the
  profile's last scan date did not move). [ADO-02] The suspected cause, read in the task's code:
  it hands credentials to its wrapper in variables named `VERACODE_API_KEY_ID` and
  `VERACODE_API_KEY_SECRET`, and the group's secrets of the same names are dropped from the
  environment. [ADO-03~] Not shown by an experiment in a job without the group. Consequence:
  rung 3 is "upload only, in a job that does not load the group", and its success is read from
  the Platform (last scan date), not from the step colour.

## Pinning without a Docker image
- A job without `container:` cannot use a pinned image. Pin downloads by SHA-256 checked before
  use (`sha256sum -c`), and by exact version. Veracode publishes no checksum for the Pipeline
  Scan zip or the CLI; the lab computed them once and stored them as template defaults. The
  Veracode API wrapper jar's SHA-1 matched Maven Central's. Old CLI versions disappear from the
  download site: the step then warns and the version needs a mirror. [ADO-07]
- Bumping a pin is a change to the template repository, released as a new tag. Not done here.

## What the lab proved
- First run (2026-11-20, one repository, per-repository steps file): +12 / -0 lines in the team's file; Pipeline
  Scan from the pipeline gave the same 12 findings as the local proof; artifact `veracode-results` held
  `results.json`. [ADO-01] One policy scan through Veracode's pinned Java API wrapper, verdict read back
  (Did Not Pass). [ADO-08]
- Shared template, `@veracode` reference pinned to tag v1.0.0 (2026-11-21), stages shape with a new stage
  `dependsOn: []` and the group on the new job: a branch run did Pipeline Scan, placement chose "none" and the
  upload was skipped; the run on `main` after the merge submitted a policy scan. [ADO-24]
- Second repository, git-flow, jar taken from the team's `package` stage with `download: current` and
  `dependsOn: package`: the run on `develop` after the merge submitted a sandbox scan, confirmed over REST to sit
  in sandbox `develop`; the policy-level scan list was unchanged. [ADO-25]
- Not proven: policy scans on tags (the `Release <tag>` name was checked offline), `@suffix@` sandbox names,
  the two-call monorepo (preview only), agent SCA, `staticScan: false`, the copied-file and extension rungs.
