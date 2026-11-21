# 01 Azure: intake

Read `01-intake.md`, then use this file for the answers. Ask in one grouped batch; accept "defaults".
Never ask for a credential value.

| # (in 01) | Azure answer and default |
|---|---|
| 1 | Organisation (name from the environment, never printed), project, repository, default branch. Default: the repository named in the request; the default branch `ado.py discover` shows |
| 2 | Branching model: infer from branches, tags, policies, pull requests (02-discovery-azure) |
| 4 | The pipeline's YAML path and name: `ado.py discover` lists "name, id, YAML path". A repository may have several pipelines: one onboarding per pipeline that builds a deployable |
| 5 | Agent pool and its tools. Needed on the agent: java, python3, curl, jq, git (and zip or python for packaging); the template's placement step uses jq and python3. Default: what the pool's agent capabilities show. Missing tool: stop and ask |
| 6 | Variable group `veracode` with `VERACODE_API_KEY_ID`, `VERACODE_API_KEY_SECRET`, `SRCCLR_API_TOKEN` (names only), open to the pipeline |
| 7 | Application profile: Default: `<repository name>` or the organisation's prefix + repository name; MEDIUM |
| 9 | Rollout stage: `audit` only |
| 10 | Who approves; **may the agent complete the pull request?** Default: no, the agent opens it and a person completes it |
| 12 | The organisation's `veracode-pipelines` repository: exists? same project? newest tag? Looked up by `ado.py discover veracode-pipelines` |

Two Azure-only questions, with defaults:

| # | Question | Default |
|---|---|---|
| A1 | The team's `trigger:` decides which branches and tags run the pipeline. Is it right that scans run only where it triggers? | yes; changing the trigger is a change to the team's lines and is asked, not done |
| A2 | Is there, or may a person add, a **build validation** policy so pull requests run the pipeline? | not changed by the agent; reported as "pull requests get no Veracode run until it exists" |

Write the answers into `templates/repo-plan.md`.
