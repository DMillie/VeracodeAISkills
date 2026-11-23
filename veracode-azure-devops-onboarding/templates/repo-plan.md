# Veracode onboarding plan: <project>/<repository> (Azure DevOps)

Date: <YYYY-MM-DD>. Agent: <name>. Status: for approval / approved by <who> at <time>.

## 0. Rung and existing state

| Item | Answer |
|---|---|
| Workflow Integration installed (project `veracode`)? | <no / yes> |
| Template repository `veracode-pipelines`: same project? tags? newest | <yes, v1.0.0 / other project / none> |
| `ado.py detect` | <not onboarded / upgrade / nothing to do> |
| **Rung and why** | <1: template by tag v..., because ... / 2: copy, because ... / 3: extension, because ...> |
| **Rollout stage** | audit (the only stage on Azure today) |

## 1. Intake (answers; (d) = default)

| Item | Answer |
|---|---|
| Organisation, project, repository, default branch | |
| Branching model | |
| Language, build, deployable | |
| Pipeline name, id, YAML path | |
| Agent pool and tools (java, python3, curl, git) | |
| Variable group `veracode` with the three names (names only) | |
| Application profile, criticality, policy | |
| Approver; may the agent complete the pull request | no |

## 2. Discovery

- Pipeline shape: <A steps-only / B jobs / C stages>. Top-level keys found: trigger <...>, pool <...>, container <...>, variables <list/mapping/none>, resources <...>.
- Branches: long-lived <...>; short-lived <...>; stale <...>. Tags <...>.
- Branch policies <...>; build validation <yes: pipeline / none>. Open pull requests <...>.
- Which branches and tags the team's trigger runs <...>.
- Existing security tooling <...>. Blockers and questions <...>.

## 3. Scan placement

| Branch or tag | Veracode steps | Parameters | Scan name |
|---|---|---|---|
| | | | |

Not covered: gate, baseline, container scan, pull requests (until build validation exists).

## 4. Packaging

- Package: <contents>; excluded <...>; built by <script>. Expected places <3 to 5 file:line>.
- Proof: candidates and counts <...>.

## 5. Planned change

- Files: `<yaml path>` (+N / -0), <new `.azure-pipelines/veracode-steps.yml` for rung 2>.
- One pull request per long-lived branch: <list>. Not completed by the agent.
- Lint: `ado.py validate` <result>.

## 6. What the branch run will and will not show

- Will run: <steps>. Will not run here: <release-ref-only steps>.
