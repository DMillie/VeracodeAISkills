# 05 Additive CI change (Azure Pipelines)

Pre-condition: the plan is approved or its defaults were pre-approved, and it names the rung
(00-integration-ladder-azure), the pipeline shape (A, B or C, from 02) and the packaging (04).
**One pull request per long-lived branch**, each from that branch, same change. Work only in a clone
under `work/`. The diff is additions only: `git diff --numstat` must show 0 deleted lines.

## Steps

1. Detect: `python3 tools/ado.py detect work/<repo>`. Continue only on `not onboarded`.
2. Branch: `git -C work/<repo> checkout -b veracode/onboarding-<branch with / as ->` from the target branch.
   `ado.py push` accepts only branch names that start with `veracode/`.
3. Edit the pipeline file as below. Then add nothing else.
4. Lint (before the push, so name the TARGET branch, which exists): `python3 tools/ado.py validate <repo> "<pipeline name>" <target branch> --file work/<repo>/<yaml path>`.
   It must print `OK` and a list that includes names starting with `Veracode:` (e.g. `Veracode: Pipeline Scan (veracode-results)`). Any error: fix the YAML, not the check.
   `validate` does not see a missing variable group or a permission gate: step 8 does.
5. Profile (agent-side): `python3 tools/ado.py profile <name>`; if absent and the plan says create it:
   `python3 tools/ado.py profile <name> --create` (`profile` was not run in the lab build; if it fails, stop and ask for the profile). Exact-name match. Never for a language without static support.
6. Commit and push: `git -C work/<repo> add -A`, `git -C work/<repo> commit -m "Add Veracode security scanning (audit stage)"`,
   `python3 tools/ado.py push work/<repo> veracode/onboarding-<branch>`.
7. Pull request:
   `python3 tools/ado.py pr-create <repo> veracode/onboarding-<branch> <target branch> --title "Add Veracode security scanning (audit stage)" --description-file <file>`.
   The description file (you write it) holds: rung and template tag, stage `audit`, the placement table, the profile and its policy,
   what runs on this branch and what only after merge, what is NOT covered (no gate, no baseline, no container scan,
   pull requests not scanned until build validation exists). A pull request to a branch with a policy may need reviewers: say who.
8. Run it. If the team's `trigger:` covers branches (no `trigger:` means all, and the push in step 6 already started a
   full run, team build included), find it: `python3 tools/ado.py runs <repo> --branch <your branch>`. Do not queue a
   second one. Only if no run exists: `python3 tools/ado.py run <repo> "<pipeline name>" <your branch>` (not run in the
   lab build). Then `python3 tools/ado.py run-wait <run id>` (playbook 06). **At most two runs per branch.** One agent runs
   one job at a time. On a branch that is not a scan ref the placement step chooses "none": only the Pipeline Scan and
   the directory scan run, the upload is skipped. That is expected.
9. Do not complete the pull request unless the person said you may. If they did:
   `python3 tools/ado.py pr-complete <repo> <pr id>` (merge strategy `noFastForward`, which works under a "Require a
   merge strategy" policy; add `--strategy squash` if the policy demands it). It refuses unless the latest run is on the
   PR's source commit and succeeded or partiallySucceeded. The merge starts a run on the target branch: **that run is
   where the policy or sandbox scan happens** (read it, playbook 06). Only one scan may be open per profile: wait until
   that run is done before completing the next pull request or starting any other run that scans.

## Rung 1: add to the pipeline file

Worked examples: `templates/azure/examples/` (`*.before.yml` is the team's file, `*.after.yml` the result). Template tag: the newest `vX.Y.Z` of `veracode-pipelines` (from `discover veracode-pipelines`). Exact tag, never a branch.
Parameters: playbook 03 (`appProfile`, `rolloutStage`, `package`, `staticScan`, `policyScanRefs`, `sandboxRefs`, `directoryScan`, `scaAgent`, `artifactName`, `sourceDir`; the tool pins are never set here). `appProfile` is required. The parameter list is also at the top of `veracode-steps.yml`
(`templates/azure/` holds the same file as tag v1.0.0); if they differ, the file in the tag wins.

### The top-level addition (all shapes)

Append at the END of the file, column 0. If the key already exists, add only the new lines under it.

```yaml
resources:
  repositories:
    - repository: veracode
      type: git
      name: veracode-pipelines
      ref: refs/tags/v1.0.0
```

- `resources:` exists with `repositories:` → append the `- repository: veracode` item (4 lines) to that list.
  `resources:` exists without `repositories:` → add the `repositories:` key and the item under it.
- The variable group goes on the NEW job (`variables: - group: veracode` inside `- job: veracode`, as in the
  shapes below), never on the team's root `variables:`. That works whether the team's root `variables:` is a list
  or a mapping, and stays additions-only. Proven in the lab on two repositories [ADO-26].
- If the template repository is in another project, `name:` would be `<project>/veracode-pipelines`; this skill does not do that (02: not open to the pipeline). Stop.

### Shape A, steps-only (`steps:` at top level)

There is no job of your own, so the group must be at the root. Append the two steps at the end of the
team's `steps:` list, same indent as the other steps. The checkout already happened; the package comes from the
files in the workspace. Also add the root group:

```yaml
variables:
  - group: veracode
```

- Root `variables:` exists in list form: append `  - group: veracode` to it.
- Root `variables:` exists as a mapping (`NAME: value`): **STOP and ask.** A group cannot sit next to a mapping
  without rewriting the team's lines into list form, which is not additions-only. Offer the person either that
  rewrite (every value unchanged, said in the pull request) or moving the pipeline to `jobs:`.
The steps:

```yaml
  - script: |
      set -eu
      out="$(Build.ArtifactStagingDirectory)/veracode"
      mkdir -p "$out"
      # PACKAGING COMMANDS from playbook 04: write "$out/veracode-package.zip"
      python3 -m zipfile -l "$out/veracode-package.zip"
    displayName: 'Veracode: package'
    continueOnError: true
  - template: veracode-steps.yml@veracode
    parameters:
      appProfile: <profile name>
```

The Veracode steps run only if the team's earlier steps succeeded. That is accepted: they come after build and deploy and cannot delay a rollout.

### Shape B, jobs (`jobs:` and no `stages:`)

Append this job at the end of the `jobs:` list, same indent as the other `- job:` items.
`pool:` is copied from the team's jobs; omit it if the team's file sets `pool:` once at the top.

```yaml
  - job: veracode
    displayName: 'Veracode'
    pool: <copy the team's pool text>
    variables:
      - group: veracode
    steps:
      - checkout: self
      - script: |
          set -eu
          out="$(Build.ArtifactStagingDirectory)/veracode"
          mkdir -p "$out"
          # PACKAGING COMMANDS from playbook 04: write "$out/veracode-package.zip"
          python3 -m zipfile -l "$out/veracode-package.zip"
        displayName: 'Veracode: package'
        continueOnError: true
      - template: veracode-steps.yml@veracode
        parameters:
          appProfile: <profile name>
```

No `container:` on this job. If the deployable is a build output of another job (Java jar), add
`dependsOn: <that job's name>` under `- job: veracode` and replace the package script by the two steps below
(proven in the lab with a jar the team's `package` stage publishes [ADO-25]). `<artifact name>` is the name in the team's
`publish:` step; the jar then lands in `$(Pipeline.Workspace)/<artifact name>`. Pass `package:` to the template:

```yaml
      - download: current
        artifact: <artifact name>
      - bash: |
          set -euo pipefail
          mkdir -p "$(Build.ArtifactStagingDirectory)/veracode"
          cp "$(Pipeline.Workspace)"/<artifact name>/<jar file name or pattern> "$(Build.ArtifactStagingDirectory)/veracode/<stable name>.jar"
        displayName: 'Veracode: take the packaged jar'
        continueOnError: true
      - template: veracode-steps.yml@veracode
        parameters:
          appProfile: <profile name>
          package: $(Build.ArtifactStagingDirectory)/veracode/<stable name>.jar
```

In shape C, set `dependsOn: <the stage that publishes the artifact>` on the new stage instead.

### Shape C, stages (`stages:`)

Append a stage at the end of the `stages:` list, same indent as the other `- stage:` items. Its job
is Shape B's job, indented under `jobs:`. `dependsOn: []` makes it independent of the team's stages.

```yaml
  - stage: Veracode
    displayName: 'Veracode'
    dependsOn: []
    jobs:
      - job: veracode
        displayName: 'Veracode'
        pool: <copy the team's pool text>
        variables:
          - group: veracode
        steps:
          - checkout: self
          - script: |
              set -eu
              out="$(Build.ArtifactStagingDirectory)/veracode"
              mkdir -p "$out"
              # PACKAGING COMMANDS from playbook 04: write "$out/veracode-package.zip"
              python3 -m zipfile -l "$out/veracode-package.zip"
            displayName: 'Veracode: package'
            continueOnError: true
          - template: veracode-steps.yml@veracode
            parameters:
              appProfile: <profile name>
```

A stage that needs the team's artifact: set `dependsOn: <the stage that publishes it>` and download as in shape B.

### Monorepo or several calls

One packaging step and one template call per application, with its own `appProfile`, `package:`, `sourceDir:`
(the application's folder, for the directory scan) and `artifactName: veracode-results-<app>`; unique step names.
The example `monorepo-two-apps` in `templates/azure/examples/` was checked with the preview only, not run.

## Rung 2: the copied file

Not run in the lab build. Copy `veracode-steps.yml` from `templates/azure/` unchanged to `.azure-pipelines/veracode-steps.yml`
in the branch (a new file; never overwrite an existing file there). Add NO `resources: repositories:`
block. Call it by path:

```yaml
      - template: .azure-pipelines/veracode-steps.yml
        parameters:
          appProfile: <profile name>
```

The path is read relative to the file that holds the call. Everything else (variable group, shapes,
parameters) is as for rung 1. The plan states why rung 1 was not used; the summary proposes moving the file to
`veracode-pipelines`. A file edited in the repository is a fork: do not edit it.

## Rung 3: the marketplace extension, upload only

Use only when the plan says so. The new job must NOT load the group: no `variables: - group: veracode` on it and none at the root
(the group is what collided: facts file [ADO-02]). Name of the service connection: from `discover`.
Append a job (shape B form; shape C wraps it in a stage). The package script is the one above.

```yaml
  - job: veracode
    displayName: 'Veracode (upload only)'
    pool: <copy the team's pool text>
    steps:
      - checkout: self
      - script: |
          set -eu
          out="$(Build.ArtifactStagingDirectory)/veracode"
          mkdir -p "$out"
          # PACKAGING COMMANDS from playbook 04: write "$out/veracode-package.zip"
          python3 -m zipfile -l "$out/veracode-package.zip"
        displayName: 'Veracode: package'
        continueOnError: true
      - task: Veracode@4
        displayName: 'Veracode: upload and scan (release point only)'
        condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
        continueOnError: true
        inputs:
          ConnectionDetailsSelection: 'Service Connection'
          AnalysisService: <service connection name>
          veracodeAppProfile: <profile name>
          version: '$(Build.SourceBranchName) $(Build.BuildId)'
          filepath: $(Build.ArtifactStagingDirectory)/veracode/veracode-package.zip
          createProfile: false
          failBuildIfUploadAndScanBuildStepFails: false
          importResults: false
          failBuildOnPolicyFail: false
          maximumWaitTime: '60'
```

Replace `refs/heads/main` with the release point. Those inputs ran in the lab [ADO-18]; the task may hold the
only agent while it waits. This rung has no Pipeline Scan, no directory scan, no sandbox. The report says so,
and says the upload is verified only by the Platform's last-scan date.

## What not to do

- Never edit or delete a line of the team's file. Never reorder. Never rewrite indentation.
- Never `ref:` a branch, never `latest`, never download a script and pipe it into a shell.
- Never add `condition:` or `continueOnError:` tricks to hide red: the template decides.
- Never put a credential value anywhere. Secrets reach scripts only through `env:` ([ADO-04~]); the template does it.
- Never change a branch policy, the variable group, a service connection, a permission, or the team's `trigger:`.
