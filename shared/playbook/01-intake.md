# 01 Intake

Ask once, in one grouped batch, with the default beside each question. Accept "defaults" as
an answer. Never ask for a credential value; ask for the variable *names* and where they live.

| # | Question | Default if unanswered |
|---|---|---|
| 1 | Which repository (SCM, group/project path) and which branch is the default? | the project named in the request; its default branch |
| 2 | Branching model: GitHub flow (feature -> main), git-flow (develop/release/main), trunk + tags, release branches? | inferred from branches, protected branches and tags (playbook/02) |
| 3 | Languages and build: what produces the deployable (jar, zip of source, dist, image)? | inferred from the CI file and manifests |
| 4 | Where is the CI config (`.gitlab-ci.yml` in the repo, another path, another project)? | the project's `ci_config_path`, default `.gitlab-ci.yml` |
| 5 | Runners: architecture (x86_64 or arm64), docker executor, docker-in-docker allowed, outbound HTTPS to Veracode hosts? | x86_64 docker executor with dind (check the runner list) |
| 6 | Credential variable names and scope: HMAC API ID/key of an API service account, CI-type SCA agent token — on the group or the project, masked, unprotected? | `VERACODE_API_KEY_ID`, `VERACODE_API_KEY_SECRET`, `SRCCLR_API_TOKEN` on the group |
| 7 | Application profile: naming convention, business criticality, team, policy? | `<repo name>` (or the organisation's prefix convention), MEDIUM, default team and policy |
| 8 | Which scan types are licensed: SAST (Pipeline + Upload and Scan), SCA (agent), Container? | all three |
| 9 | Rollout stage: `audit`, `warn`, `block-new` or `block-policy` (playbook/00)? Any reason to override the application's Veracode policy with a severity list? | `audit` for the onboarding MR, with a recommendation to move to `block-new` once the target branch has a baseline; criteria = the policy assigned to the application profile, no override |
| 10 | Who approves the plan, and may the MR be merged by you? | the requester approves; the MR is opened, never merged by the agent |
| 11 | Scan naming convention for the Platform (so "last release scan" is findable later)? | `Release <tag>` on tags, `<branch> <short sha>` otherwise |
| 12 | Is a vendor-maintained integration installed for this SCM, or does the organisation already own a shared Veracode template/component? Where, which release? | looked up in discovery (playbook/00, 02); if neither exists the platform team is asked before a central project is created |

Roles needed on the API service account (names only): upload and submit (`uploadapi`,
`submitterapi` or `apisubmitanyscan`) for Upload and Scan, `greenlightapiuser` for the Pipeline
Scan; see reference/platform-facts.md "Credentials and roles". The SCA agent token must be
**CI-type**; a CLI activation token is rejected, and an API service account cannot create one.

Write the answers (and which were defaults) into the Intake section of `templates/repo-plan.md`.
