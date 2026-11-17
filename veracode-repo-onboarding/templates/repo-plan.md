# Veracode onboarding plan: <group/project>

Date: <YYYY-MM-DD>. Agent: <name>. Status: for approval / approved by <who> at <time>.

## 0. Integration rung and existing state

| Item | Answer |
|---|---|
| Vendor-maintained integration installed for this SCM (rung 1)? | <no / yes: …> |
| Organisation shared unit (rung 2): project, visibility, newest release | <platform/veracode-ci, internal, X.Y.Z / none> |
| Readable by this project's members (lint with a member token)? | <yes / no: error> |
| Already integrated (`tools/detect_integration.py`)? | <mode, version → onboard / upgrade / pin / migrate / review / nothing to do> |
| **Rung used and why** | <2: component `…/veracode@X.Y.Z` included by reference, because rung 1 is not available on … / …> |
| Include form | <component / project+ref+file (why) / per-repo copy (why)> |
| **Rollout stage** | <audit / warn / block-new / block-policy>; next: <stage> when <condition> |
| Gate criteria | policy `<name>` assigned to the application profile <or override: severities …, reason, approver> |

## 1. Intake (answers; (d) = default used)

| Item | Answer |
|---|---|
| Repository, default branch | |
| Branching model | |
| Languages, build, deployable | |
| CI config location | |
| Runners (arch, executor, dind, egress) | |
| Credential variable names and scope (names only) | |
| Application profile name, criticality, team, policy | |
| Scan types licensed | |
| Rollout stage (see section 0) | |
| Approver; may the MR be merged by the agent | no |
| Scan naming convention | |

## 2. Discovery

- CI: stages <…>; jobs <…>; images <…>; caches <…>; includes <…>; dind <yes/no>.
- Build output: <job> → <path>.
- Manifests: <…>. Dockerfile: <yes/no, context>.
- Branches: long-lived <…>; short-lived pattern <…>; protected <…>; tags <…>.
- Pipelines now: <green/red, last ids>.
- Variables present (names): <…>, masked <…>, protected <…>.
- Runner: <name, arch, executor, online>.
- Existing security tooling: <none/…>.
- Blockers / questions for the human: <none/…>.

## 3. Scan placement

| Branch / event | Jobs | Gate | Baseline from | Scan name |
|---|---|---|---|---|
| | | | | |

Fork MRs: <no credentials; jobs skipped / n.a.>.

## 4. Packaging

- Artifact: `<name>` produced by job `<name>`: <contents>; excluded: <…>.
- Check: <listing expected>.

## 5. Planned change

- Append to `.gitlab-ci.yml`: the component include with inputs <list> <and the packaging job `…`>.
  No job definitions copied, no existing job changed. Expected diff: +N / −0 (N ≈ 15–40).
- Jobs the component will create per ref (dry run): <ref: jobs; …>.
- Application profile `<name>`: <exists / will be created> (criticality <…>).
- MR: branch `veracode-onboarding` → `<target>`, title "Add Veracode security scanning". Not merged by the agent.

## 6. What this MR's pipeline will and will not show

- Will run: <jobs>. Rollout stage <audit>: <nothing blocks; no baseline yet>.
- Will not run here (release point only): <jobs>.
