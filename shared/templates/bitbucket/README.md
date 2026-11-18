# Bitbucket Cloud Pipelines: draft

**Not run on Bitbucket.** The step scripts in `examples/` were run locally in the pinned images
(`tests/bitbucket/run.sh` in the source repository); the pipeline file itself has not executed
on Bitbucket's runners. Facts and their sources: `reference/facts/bitbucket.md`.

What differs from the GitLab component:

- There is no vendor integration and no include-by-reference for single steps, so the steps live
  in each repository's `bitbucket-pipelines.yml` (rung 3). An organisation that wants one shared
  definition builds a custom pipe from these scripts or, on Premium, exports whole pipelines.
- Only the `audit` rollout stage exists. No baseline, no new-findings gate, no sandbox scans,
  no SCA agent step, no container scan.
- The release-point policy scan is submitted and not waited for, because waiting costs build
  minutes.
- Results are shown in Bitbucket through a Code Insights report on the commit.
