# 00 Azure: before the first onboarding (for the person who owns the project)

The agent onboards ONE repository. It never creates projects, repositories, variable groups, permissions or
policies, so these six things must exist first. Each has a check; `discover` is read-only. If one is missing the
agent stops and says which. Do this once per Azure DevOps project, then hand the agent a brief
(`templates/onboarding-brief.md`).

Agent's environment (names only, values never shown to the agent or written anywhere): `AZURE_DEVOPS_ORG`,
`AZURE_DEVOPS_PAT`, `AZURE_DEVOPS_PROJECT` (or pass `--project <project>` on every `ado.py` call), and for the
profile tool and local packaging proof `VERACODE_API_KEY_ID`, `VERACODE_API_KEY_SECRET`.

## 1. Variable group `veracode`

- **Do:** Pipelines > Library > variable group named exactly `veracode` with `VERACODE_API_KEY_ID`,
  `VERACODE_API_KEY_SECRET` and (for agent-based SCA) `SRCCLR_API_TOKEN`, each marked secret. Use an API service
  account's credentials, not a person's. Allow the pipelines that will be onboarded to use the group (the group's
  Pipeline permissions; the lab opened it to all pipelines of the project through the REST API, the web pages were
  not clicked through). [ADO-35]
- **Check:** `python3 tools/ado.py discover <repository>` lists `veracode` with the three names under "variable groups".
  It cannot show whether a pipeline is allowed to use it: a pipeline that is not fails before its first step. [ADO-12~]
- **If missing:** the agent stops. It never creates or edits a group.

## 2. Template repository `veracode-pipelines`

- **Do:** create a repository named `veracode-pipelines` in the SAME project as the repositories to onboard (a
  pipeline's token reaches only its own project [ADO-14]). Commit `templates/azure/veracode-steps.yml` (and its
  README) to `main`, tag the commit `v1.0.0`, and never move a released tag: a change is a new tag. Then open the
  repository to the project's pipelines (the repository's Pipeline permissions, under its security settings). The lab
  opened it to all pipelines through the REST API and the consumers then ran without a wait. [ADO-35]
- **Check:** `python3 tools/ado.py discover veracode-pipelines` shows the repository and its tags.
- **If it is not opened:** the first run of each consumer waits at "needs permission" until a person clicks
  **Permit** on that run. `ado.py run-wait` prints `WAITING FOR PERMISSION` and the agent asks for you; this is the one
  click it cannot make. Deleting and re-creating a pipeline loses the permit. [ADO-13]
- **If the repository is missing or in another project:** the agent stops, or, only with your approval, copies the
  file into the repository (rung 2, not run in the lab).

## 3. Build agent

- **Do:** a Linux x64 agent in the pool the pipelines use, with `java`, `python3`, `curl`, `jq`, `git` and `zip` on
  it. The template downloads the Veracode tools itself and checks their SHA-256; no Docker is needed. A free-tier
  self-hosted pool runs one job at a time, so runs queue (waits of 10 to 30 minutes were normal). [ADO-21] [ADO-29]
- **The Veracode job must not be a container job.** It runs on the agent and uses the agent's tools. In a team's build
  image the steps failed with exit 127 (no `python3`, no `jq`). `ado.py validate` warns when the Veracode steps sit
  inside a container job. [ADO-37]
- **Check:** `discover` lists the pools and the agent's capabilities. Tested: one self-hosted Linux agent. Not tested:
  Microsoft-hosted, Windows or arm64 agents.

## 4. One Veracode application profile per repository

- **Do:** create the profile in the Veracode Platform (name, business criticality, policy), or let the agent do it by
  saying so in the brief: it then runs `python3 tools/ado.py profile <name> --create`. The pipeline template never
  creates a profile; a wrong name is refused, nothing is created. A monorepo needs one profile per application.
- **Check:** `python3 tools/ado.py profile <name>` (exact name). Reading an existing profile this way worked in the lab
  tests; `--create` was not run. [ADO-39]

## 5. The agent's Azure DevOps token

What the token must be able to do, in the project, **derived from the calls `tools/ado.py` makes; the lab did not
record its token's scopes and no minimal token was tested** [ADO-34~]:

| Needed for | Capability |
|---|---|
| `discover`, `clone`, `runs`, `run-wait`, `run-log`, `artifact`, `pr-status` | read: repositories, branches, tags, pull requests, branch policies; pipelines and runs with logs and artifacts; agent pools; variable group names; service connection names; environments |
| `push` | create branches named `veracode/...` and push commits to them (never a team branch, never a force push) |
| `pr-create`, `pr-complete` | create a pull request; complete it only when the brief allows (the merge must satisfy the target's branch policies) |
| `validate`, `run` | call the pipeline preview (a dry run) and queue a run of an existing pipeline |

Nothing else: no project, policy, permission, variable group or pipeline-definition changes. Give it a token of its
own that expires, not a person's full-access token.

## 6. What stays yours

- **Pull requests get no Veracode run** until you add a build validation policy on each protected branch. Without it,
  the push of the PR's source branch gives a Pipeline Scan run only if the team's `trigger:` covers that branch. [ADO-10~]
- **Nothing blocks.** `audit` is the only rollout stage: no gate, no baseline. Policy verdicts are submitted, not waited for.
- **Tags are not protected** in Azure Repos (a "Create tag" permission instead). [ADO-22]
- Not in the template: container scan, DAST, fixing findings, mitigations.

## Which model

Results of the lab tests, 2026-11-21 and 22, each run one sample (a pass is not proof): [ADO-36]

- Claude Sonnet and Claude Haiku each passed all four test repositories (trunk TypeScript, git-flow Java, Go with a
  submodule, Java monorepo) on the current skill text, in 6 to 60 minutes. Sonnet failed one repository before a
  wording fix; Haiku needed two reminders on one repository that a queued run is not a blocked one.
- Five local open-weight models (12B to 35B parameters) were tried on the easiest repository: one passed, in 97
  minutes against 6. The same model passed the git-flow repository in 145 minutes and ran out of a 3-hour cap on the
  monorepo. Two of the others reported work that had not happened.
