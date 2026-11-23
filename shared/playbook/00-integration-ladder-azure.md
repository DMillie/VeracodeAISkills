# 00 Azure: the integration ladder

Read `00-integration-ladder.md` first (it is SCM-neutral: rungs, rollout stages, re-runs).
This file replaces its GitLab words with Azure DevOps ones. Where the two differ, this file wins.

## The three rungs on Azure DevOps

The numbers below are the Azure numbers and replace the neutral file's. What the neutral file calls rung 1 (vendor integration) is called "Workflow Integration" here and has no number.

| Rung | What it is | Use it when | You do |
|---|---|---|---|
| 1 | **The organisation's template repository `veracode-pipelines`**, called by tag from the pipeline | the repository `veracode-pipelines` exists in the SAME project as the pipeline, has a tag `vX.Y.Z`, and `ado.py discover` shows the pipeline may use it. **This is the default when it exists.** Proven in the lab (`@veracode` pinned to a tag, two repositories) [ADO-24][ADO-25] | add `resources: repositories:` pinned to the newest tag and one `- template:` call ([05](05-ci-change-azure.md)) |
| 2 | **The same steps file copied into the repository**, `.azure-pipelines/veracode-steps.yml` | rung 1 is impossible: no such repository, or it is in another project, or the pipeline cannot read it, and a person says it cannot be fixed now | copy the file from `templates/azure/` unchanged, call it by path. The plan says why rung 1 was not used. Not run in the lab build |
| 3 | **Veracode's marketplace extension task** (`Veracode@4`), upload only | the template cannot run at all (for example the agent has no java, python3, curl or jq) and the extension is installed | one job with the task. No Pipeline Scan, no directory scan. Not run in the lab build. See the unconfirmed finding below |

The Workflow Integration is Veracode's Azure DevOps Workflow Integration:
a `veracode` project and webhooks in the organisation. If `ado.py discover` lists a project named
`veracode`, or the person says it is installed, add NO jobs; report and stop.

## The extension task is last because of an unconfirmed finding

In the lab, `Veracode@4` with its service connection ended green and uploaded nothing in a job that
also loaded variable group `veracode`. The suspected cause (credential variable names that collide
with the group's secrets) was read in code and is **unconfirmed** [ADO-03~]; the colliding run is
[ADO-02]. The extension has no Pipeline Scan task [ADO-17~]. So rung 3 is upload only, only in a job
that does not load the group, and its success is read from the Platform, not from the step colour.

## When to stop and ask a person (do not work around)

| You see | Say | Never |
|---|---|---|
| `veracode-pipelines` exists but in another project | "It is not open to this project's pipelines (tokens stay in their project). Move or copy it into project X, or approve rung 2." | create the repository, change project settings |
| The run waits at "needs permission" for the repository `veracode-pipelines` | "Please click Permit on run <id> (pipeline <name>)" | retry, delete the pipeline |
| Variable group `veracode` missing, or not usable by this pipeline | "Create or authorize group `veracode` with the three variable names" | create the group, read values |
| No tag `vX.Y.Z` in `veracode-pipelines` | "Which release shall I pin?" | pin a branch |
| `veracode-pipelines` has a tag but you cannot read it | "I cannot read it; who owns it?" | copy it from memory |
| The pipeline file uses `extends:` | "The file extends a required template; adding steps is the owners' decision." | edit it |

## Re-runs on an onboarded repository

`python3 tools/ado.py detect <dir>` prints one of:

| Output | Action |
|---|---|
| `nothing to do` | report rung, tag, stage; stop |
| `upgrade`, detail says a template reference | a one-line pull request that changes `ref: refs/tags/<old>` to the newest tag; read the template repository's tag notes into the description |
| `upgrade`, detail says an in-repo copy | do not edit the copy. Report it and ask whether to move to rung 1 (a pull request replacing the copy by the reference) |
| `not onboarded` | steps 1 to 6 |

Any other Veracode step in the file (hand-written, extension task) with `not onboarded`: report it, add nothing, ask.

## Rollout stage

Template 1.0.0 supports only `audit`: nothing fails the run; tool problems are warnings. Stages
`warn`, `block-new`, `block-policy` and baselines do not exist on Azure yet. Do not promise them.
