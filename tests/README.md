# Tests

Three tiers. Run the first on every change; run the others before a release or after
editing anything an assistant reads first (`SKILL.md`, `AGENTS.md`, the playbooks).

| Tier | Command | Needs | Takes | What it catches |
|---|---|---|---|---|
| Static | `tests/static/run.sh` | python3, node, bash | seconds | copies out of step with `shared/`, evidence IDs without an entry, broken front matter, dead paths, scripts that do not parse, a decisive rule removed or reworded, tool regressions, lab names or secret-looking strings |
| GitLab | `tests/gitlab/run.sh` | a GitLab with the component released; `GITLAB_URL`, `GITLAB_TOKEN`, `LINT_PROJECT` | a minute | the component and examples no longer lint, job sets per ref change, gate exit codes per rollout stage change |
| Behaviour | scenarios below | a lab: sample repositories with answer keys, a Veracode tenant, an agent to drive | 10 to 60 minutes each | an assistant given the skills picks the wrong one, places scans wrongly, accepts a wrong package, or reports what it did not verify |

## The rules that must not disappear

`tests/static/required-rules.tsv` lists the sentences that decided outcomes in testing
(file, pattern, reason). Removing or rewording one fails the static tier. If the
rewording is intended, change the line in the same commit so the reviewer sees both.

## Behaviour scenarios

Each scenario gives an agent a run folder with the skills installed as folders, a brief,
and nothing else. The agent must first choose a skill from the front matter alone and
write the choice down; then do the job. A script grades the outcome from files, the
GitLab API and saved scan results. The agent never sees an answer key.

| Kind | The agent does | Graded on |
|---|---|---|
| Routing | reads the five descriptions and assigns `behaviour/routing.json` requests to skills | each answer against the expected skill |
| Placement | reads one repository and writes where each scan belongs; changes nothing | release point, application profiles, per-branch scan fields against the key (90%), no writes made |
| Packaging | builds candidate packages and runs real Pipeline Scans | at least two candidates, reported count backed by a saved result, count equals the proven count, key locations present |
| Onboarding | the whole job on a live GitLab project | merge request merged, component pinned to an exact version, additions only, pipeline scan ran, pipeline result equals the proven count, limits stated, no credential written |

`behaviour/routing.json` is in this repository. The other kinds need sample repositories
with planted flaws and keys; those and the runner live with the lab, not here. One run
per scenario is one sample: a pass is not proof, and a fail on a model that passed before
is the signal worth reading.

## Bitbucket

- Static: `tests/static/test_bitbucket.py` (part of the static tier) checks the draft pipeline's structure, pins, credentials handling and that it cannot start two pipelines for one pull request.
- Local steps: `tests/bitbucket/run.sh <example.yml> <source dir> <work dir> [expected findings]` runs the package, scan and report step scripts in their pinned images. Needs docker and Veracode credentials in the environment; uses one Pipeline Scan.
- Not covered: anything on Bitbucket itself. No pipeline has run there.
