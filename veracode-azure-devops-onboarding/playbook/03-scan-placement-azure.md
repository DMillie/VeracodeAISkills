# 03 Azure: scan placement

Read `03-scan-placement.md` for the principles and the branching-model table. Ignore its GitLab
parts: the "inputs of the GitLab component" table, baselines, `gate_skip_branches`, fork merge
requests. This file replaces them. Where the two differ, this file wins.

## What the Azure template can do (template tag v1.0.0)

- A "placement" step first decides from the ref of the run what the upload step does: policy, sandbox or none. It needs jq and python3 on the agent. Steps it skips show as skipped.
- Pipeline Scan on every run (when `staticScan` is true). Results in the artifact. **No gating
  and no baseline:** `audit` only.
- Directory scan (dependencies, secrets, IaC) on every run (`directoryScan`), of `sourceDir`.
- Policy scan on runs whose ref starts with a prefix in `policyScanRefs`; submitted, not waited for.
  A tag ref gives the scan the name `Release <tag>`; other refs `<branch> <short sha>`.
- Sandbox scan on runs whose ref starts with a prefix in `sandboxRefs` (created if missing).
- Policy prefixes are tested BEFORE sandbox prefixes. Matching is by prefix: `refs/heads/main` also
  matches `refs/heads/main-old`; `refs/tags/v` also matches `refs/tags/v1.0.0-rc.1`.
- Agent-based SCA: `scaAgent: false` by default; turn it on only for an ecosystem the SCA agent supports.
  Not run in the lab.
- No container scan. Say "not covered".
- Only one scan may be open per profile: when several branches are merged one after another, wait for each
  target-branch run to finish before the next merge.

## From the model to parameters

Anything not listed stays at its default. `policyScanRefs` is a list of ref PREFIXES (`refs/heads/main`),
`sandboxRefs` a list of `{prefix, sandbox}`, first match wins. In a sandbox name `@suffix@` is the part of the
ref after the prefix, with `/` and `.` turned into `-` (prefix `refs/heads/release/` and name `release-@suffix@`
give `release-2-5` for `release/2.5`). The lab proved this on a git-flow repository (sandbox `develop` from the
develop branch) [ADO-25]; `@suffix@` and tags were not run.

| Model | Parameters |
|---|---|
| GitHub flow (main ships) | none: `policyScanRefs` default is `['refs/heads/main']` [ADO-24] |
| git-flow (the example `git-flow-java` in `templates/azure/examples/`) | `policyScanRefs: ['refs/tags/v']`; `sandboxRefs: [{prefix: 'refs/heads/develop', sandbox: develop}, {prefix: 'refs/heads/release/', sandbox: 'release-@suffix@'}]`. `main` and feature branches get the Pipeline Scan only. A pre-release tag such as `v1.2.0-rc.1` also matches `refs/tags/v` and gets a policy scan (the neutral file wants a shared sandbox `prerelease`; the template cannot, because policy prefixes win and there are no regular expressions [ADO-20]): say so in the plan |
| Trunk + tags | `policyScanRefs: ['refs/tags/v']`, same pre-release limit |
| Trunk, main deploys (the example `trunk-typescript`) | none: policy scan once on `main`, no sandbox |
| Environment branches (main to staging to production) | `policyScanRefs: ['refs/heads/production']`; `sandboxRefs: [{prefix: 'refs/heads/main', sandbox: main}]` |
| Release branches | `sandboxRefs: [{prefix: 'refs/heads/release/', sandbox: 'release-@suffix@'}]`; `policyScanRefs` the ref that ships |
| Monorepo (the example `monorepo-two-apps`) | one packaging step and one template call per app: own `appProfile`, `package`, `sourceDir`, `artifactName` (`veracode-results-<app>`), unique job or step names. Preview-checked only, not run |
| No static support for the language | `staticScan: false`; keep `directoryScan`; no profile if only incidental scripts (rule 7). Not run in the lab |

Policy scans on tags are NOT proven (the `Release <tag>` name was checked offline only).

## Runs only happen where the team's trigger allows

The refs above scan only if the team's own `trigger:` starts a run there. A tag-based policy scan
needs `tags: include:` in the trigger. If the trigger lacks it, **do not edit the team's trigger**:
write "policy scan configured, will not run on tags until the trigger lists them" in the plan and
ask. Pull requests run the pipeline only through a build validation policy, which a person adds
[ADO-10~]. Until then there is no Pipeline Scan before merge; the plan says so in the first paragraph.

**Known limit: pull requests are not scanned.** All lab agents reported it. A person must add the policy:
Project settings > Repositories > the repository > Policies > the protected branch > Build validation > the
pipeline. The agent does not add it. With `trigger` on all branches, the push of the PR's source branch already
produces a Pipeline Scan run that the reviewer can read (find it with `ado.py runs <repo> --branch <source>`). [ADO-10~] [ADO-27]

Packaging: the job writes `$(Build.ArtifactStagingDirectory)/veracode/veracode-package.zip` (the
template's default `package`). Playbook 04 says what goes in.

## Gate wording for the plan

"Rollout stage `audit`. Nothing fails the run; tool problems are warnings. No baseline and no gate
exist on Azure DevOps yet. Policy scan on `<refs>` submits and does not wait; the verdict is read on
the Platform." Pull requests from forks: not checked in this skill; list it as an open question.
