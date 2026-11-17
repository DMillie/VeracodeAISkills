# Changelog

## 1.3.1
- Fixes 1.3.0, which does not parse (a colon in an input description). Do not use 1.3.0.

## 1.3.0 (broken, superseded by 1.3.1)
Found by the first real onboarding runs on Kotlin, PHP, Scala and Rust repositories (2026-11-12).
Defaults unchanged; upgrading is the one-line version bump.
- Pipeline Scan and baseline jobs wait and retry (up to 5 times) when the Pipeline Scan API
  answers HTTP 429 (6 submissions per minute per API user).
- Policy and sandbox scan jobs that waited print the Platform's pre-scan result (modules
  selected, issues): the proof that the package was the right one.
- `app_name` may stay empty with `static_scan: false`.
- SCA summary lines also match the Gradle/sbt/Composer agent output ("Total Libraries", "Direct Libraries").

## 1.2.0
Found by the blind placement test on eight repositories (2026-11-12). No input removed or
renamed, defaults unchanged: upgrading from 1.1.0 is the one-line version bump. Pins unchanged.
- `static_scan` (default true): false drops every static job for languages Veracode Static does
  not analyse; SCA, directory scan and container scan stay.
- `job_suffix`, `source_dir`, `changes_paths`: several applications in one repository, one
  include per application; job names and the baseline package carry the suffix.
- `sandbox_tags`, `sandbox_tag_name`: pre-release tags go to one shared sandbox.
- `gate_skip_branches`: deploy branches get neither the gate nor a baseline.
- `container_needs`, `container_image`: the container scan can use the team's build output or
  pull the image the team already pushed.
- README: how the policy verdict can hold a deploy (`release_stage`).

## 1.1.0
- New input `release_stage` (default `.post`): `veracode-policy-scan` and `veracode-sandbox-scan`
  now run in GitLab's last stage instead of `stage`. Found in the first proof run: on the release
  branch the team's `build` stage waited for the policy scan verdict (about 10 minutes). No
  input removed or renamed; upgrading is the one-line version bump. Pins unchanged.

## 1.0.0
- First release: policy-resolve, pipeline-scan (policy-driven, rollout stages), baseline,
  policy-scan, sandbox-scan, sca (pinned agent 3.8.125), cli-directory-scan and container-scan
  (pinned Veracode CLI 2.55.0). Images pinned by tag and digest.
