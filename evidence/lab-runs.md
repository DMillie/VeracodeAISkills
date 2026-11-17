# Lab runs: what was tested, and what was not

Status on 2026-11-12. Lab only: a self-managed GitLab CE 19.5 with one docker runner and a US
commercial Veracode test tenant. Numbers come from the onboarding agents' own reports, checked
against saved scan evidence where stated. One run per repository. The sample apps and their
answer keys were written by the same model family that was tested; agents never saw the keys.

## Worked

| Claim | Evidence |
|---|---|
| An agent with only these files finds the branching model and places each scan type | 8 of 8 repos; 339 of 370 field checks agree with the keys; every decoy branch, tag and stale README rejected |
| The agent builds a package the Platform accepts on the first pipeline run | 9 of 9 statically supported repos: Java, Kotlin, Scala, C#, Python, Go, PHP, Rails, TypeScript |
| The agent reaches a separately proven package without seeing it | four repos with packaging traps: finding counts equal to or above the builder's key |
| "Prove the package" catches wrong packages that scan green | obfuscated jar (3 instead of 9), pnpm workspace file (0 instead of 12), single-file .NET publish (nothing scanned), API and worker in one zip (worker's finding dropped) |
| One shared GitLab component covers every repo shape tried | 1.3.1: monorepo, several artifacts, per-app tags, release lines, static off, container scans; 152 checks in the test suite |
| The CI change is additions only | 19 to 97 lines per `.gitlab-ci.yml`, one include per deployable |
| The agent says so when a language is not supported | Rust: static off, no profile, stated in the report |
| Sandbox on long-lived branches, policy scan only at the release point | 8 repos, read back from the Platform |

## Smaller models (packaging step only, one run per cell)

The files name the traps, so this is not a blind test.

| Model | Result |
|---|---|
| Claude Haiku, Sonnet, Opus | correct package on both repos tried (12 of 12 and 20 of 20 findings) |
| Gemma 4 12B, local, 16 GB GPU | correct package and report, twice; its report mis-stated which expected places were found |
| Qwen3-Coder 30B, local | correct package in 1 of 5 runs |
| Devstral Small 2 24B, local | never ran a scan |

Giving the model an MCP server or a checker script instead of plain files changed no outcome.

## Veracode CLI local scan (v2.55.0, one repository, 2026-11-17)

`veracode scan static` on the TypeScript pnpm workspace: status `SUCCESS`, 22 findings reported,
12 correct. The workspace-root artifact found all 12. Three per-package artifacts repeated 10 of
them under shorter file paths and missed the two cross-package findings. Two npm build warnings,
exit still successful. Needs a URL-style `origin` remote. Not tested on any other repository, and
`veracode fix` was not tested at all.

## Did not work

| What | Detail |
|---|---|
| Go module behind a `replace` directive | 17 of 20 findings on the full onboarding run: the agent read the docs line about `replace` and kept it because the scan accepted the package. The rule "accepted is not analysed" was added afterwards |
| Terraform-only repo | the agent created an application profile for a 62-line helper script, which then reads Pass for the repository |
| One .NET release verdict | policy scans at the tag sat 60 minutes in pre-scan, then failed. Cause unknown. Packaging was proven by Pipeline Scan and sandbox; the release verdict was not |
| Component 1.3.0 | released unlinted and does not parse. Never pin it |

## Not tested

- Any SCM other than self-managed GitLab: GitHub, Azure DevOps, Bitbucket, gitlab.com.
- The Veracode GitLab Workflow Integration.
- `block-policy` at the release point on a live pipeline; merge-request-event pipelines.
- Android.
- Full onboarding (discovery, placement, CI change) on any model below the top tier.
- Engineering confirmation of why results were thin on Kotlin, Scala, PHP and Rails.
- The skills as installed skills: every run above used the plain files with `AGENTS.md` as the entry point. The behaviour suite in `tests/behaviour/` exists to close this.
