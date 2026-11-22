# Azure DevOps: the shared Veracode steps template

One file, `veracode-steps.yml`: a STEPS template that runs Pipeline Scan, directory scan, optional agent SCA and a
policy OR sandbox scan (chosen by the ref), then publishes the results as a pipeline artifact. It lives in repository
`veracode-pipelines`, released by tag, and a repository consumes it by reference, pinned to an exact tag. It is the
first rung of the Azure ladder (`playbook/00-integration-ladder-azure.md`). `veracode-steps.yml` here is an identical copy of the released file, for reading and for the
fallback rung. Source of truth: the template repository, tag in `CHANGELOG.md` of that repository.

Facts that decide how it is used:

- The template repository must be in the SAME project as the consumer: a pipeline's token cannot read repositories of
  other projects. It must be open to the pipelines (Pipeline permissions of the repository, or no restriction).
- The pipeline must name the variable group `veracode` (secrets `VERACODE_API_KEY_ID`, `VERACODE_API_KEY_SECRET`,
  `SRCCLR_API_TOKEN`). Put it on the job that calls the template (`variables: - group: veracode`): that keeps the change
  additions-only when the team's root `variables:` is a mapping. The template maps each secret with `env:` itself.
- The CONSUMER packages. The template scans the file in `package` (default
  `$(Build.ArtifactStagingDirectory)/veracode/veracode-package.zip`). Packaging rules: `playbook/04-packaging.md`.
- The `resources:` block names the repository by `name: veracode-pipelines` (same project) and `ref: refs/tags/vX.Y.Z`.
  A branch ref or a missing ref is wrong. To upgrade, change the tag.
- The agent needs java, python3, curl, jq (self-hosted Linux; no Docker needed). Microsoft-hosted agents were not tried.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `appProfile` | required | application profile, exact name, must exist; never created by the template (`ado.py profile`) |
| `rolloutStage` | `audit` | only `audit` in 1.0.0 |
| `package` | `$(Build.ArtifactStagingDirectory)/veracode/veracode-package.zip` | file to scan: zip, jar, war |
| `staticScan` | `true` | `false` = no Pipeline Scan, no policy/sandbox scan (language without Static support) |
| `policyScanRefs` | `['refs/heads/main']` | ref PREFIXES with a policy scan. A tag prefix such as `refs/tags/v` names the scan `Release <tag>` |
| `sandboxRefs` | `[]` | `[{prefix, sandbox}]`, first match wins, policy refs first; sandbox created if missing; `@suffix@` = ref after the prefix with `/` `.` as `-` |
| `directoryScan` | `true` | CLI directory scan of `sourceDir` |
| `scaAgent` | `false` | agent-based SCA (`SRCCLR_API_TOKEN`); not for pnpm; the build tool must be on the agent |
| `artifactName` | `veracode-results` | pipeline artifact; one distinct name per call in a pipeline (monorepo) |
| `sourceDir` | `$(Build.SourcesDirectory)` | app folder for directory scan and SCA (monorepo) |
| tool pins | in the file | versions and SHA-256 of Pipeline Scan, CLI, API wrapper, SCA agent: bumped only by a new release |

"Which branch scans where" is written in `policyScanRefs` and `sandboxRefs` and nowhere else. A ref in neither list
gets the Pipeline Scan only. A tag only has a pipeline run if the team's `trigger:` lists tags.

## Adding it: three pipeline shapes

Add to the repository's own file; never remove or reword a team line. In every shape: the `resources:` block once (top
level), the `veracode` job with `variables: - group: veracode`, `- checkout: self`, the packaging step(s), then
`- template: veracode-steps.yml@veracode`.

1. **Stages** (`stages:` > `jobs:`): append a stage `veracode`. `dependsOn: []` (runs beside the team's stages, needs
   no build output: source zips) UNLESS the package is a build artifact: then `dependsOn: <the stage that publishes
   it>` and `- download: current` / `artifact: <name>` in the job. Examples: `trunk-typescript`, `git-flow-java`.
2. **Jobs** (`jobs:` at the root, no stages): append a job `veracode`; `dependsOn: <build job>` only if it needs the
   build's artifact, else none.
3. **Steps only** (`steps:` at the root, one implicit job): append the packaging step(s) and the template call at the end
   of the team's list, so they run after the team's own steps (the checkout is already done), each with
   `continueOnError: true`. The variable group has to be at the root: add `variables: - group: veracode` as a root
   list. If the team's root `variables:` already exists as a mapping (`NAME: value`), a group cannot be added next to it
   without rewriting those lines into list form (`- name:` / `value:`): that is the one change that is not additions-only;
   make it, say so in the pull request, and keep every variable's value unchanged. Convert the pipeline to `jobs:` only
   if the team agrees.

**Gotcha: pipefail and `head`.** A packaging step under `set -o pipefail` that ends in `... | head -3` exits 1 when
`head` closes the pipe: the zip is fine, the step shows failed. Do not pipe listings into `head` under pipefail (use
`sed -n 1,3p`, or drop pipefail for that line). [ADO-30]

**Gotcha: `docker run` in a packaging step.** When the agent's Docker daemon is not the agent's own machine (a sidecar or
remote daemon, as in the lab), the daemon sees only the agent's work folder. Keep every folder you mount into a container
under `$(Build.SourcesDirectory)`, `$(Build.ArtifactStagingDirectory)` or `$(Agent.TempDirectory)`; a mount of `/tmp/...` is empty inside
the container and the package comes out empty (22-byte zip, Pipeline Scan says "No files found"). [ADO-33]

**Gotcha: jars on a reused workspace.** Empty the download folder and require exactly one jar (`examples/git-flow-java.after.yml`). [ADO-28]

Always run `ado.py validate <repo> <pipeline> <branch> --file <the new file>` before pushing: it must print the
Veracode step names. The preview does not run anything and cannot see a wrong profile name or a missing variable.

Several applications in one pipeline: one packaging step per app, then one template call per app with its own
`appProfile`, `package`, `sourceDir`, `artifactName` (example `monorepo-two-apps`).

## Fallback rung: no shared repository available

Only when the project cannot read a central template repository and that cannot be fixed (say why in the plan): copy
`veracode-steps.yml` to `.azure-pipelines/veracode-steps.yml` in the repository and call it WITHOUT `@veracode` and
without the `resources:` block:

```yaml
      - template: .azure-pipelines/veracode-steps.yml
        parameters:
          appProfile: my-app
```

The copy is the repository's to maintain: note the version it was copied from at the top of the file in a comment
line. `ado.py detect` reports such a copy as `upgrade`. Never edit the copy to change behaviour: ask the template owners.

## Examples

`examples/<name>.before.yml` is the team's file as found, `.after.yml` is the onboarding result: every line of
the before file is kept, nothing is removed or reworded.

| Example | Shape | Placement and why |
|---|---|---|
| `trunk-typescript` | stages, `dependsOn: []`, source zip | trunk: no sandbox; policy scan once on `main` |
| `git-flow-java` | stages, `dependsOn: package`, the team's jar | git-flow: `develop` and `release/*` to sandboxes, policy scan only on release tags `v*`, never on `main` or `release/*` |
| `monorepo-two-apps` | stages, two calls | one profile per app, distinct `artifactName` |

Checked by `tests/azure/run.sh`: offline that each after keeps every non-blank line of its before and pins a tag; online
that each after expands in the pipeline preview of a real project.
