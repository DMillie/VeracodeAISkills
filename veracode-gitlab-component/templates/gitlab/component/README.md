# veracode-ci: the organisation's Veracode CI/CD component (GitLab)

One component, `veracode`, owned by the platform/security team. Projects include it by
reference at a released version and pass a handful of inputs; nobody copies job definitions.

```yaml
include:
  - component: $CI_SERVER_FQDN/platform/veracode-ci/veracode@1.3.1
    inputs:
      app_name: my-application-profile     # Veracode application profile (must exist)
      sca_image: python:3.11               # the project's build image, for agent-based SCA
      rollout_stage: audit                 # audit | warn | block-new | block-policy
```

The project keeps one job of its own: the packaging job (default name `veracode-package`) that
publishes the artifact to scan (default `veracode-package.zip`). Everything else is in
`templates/veracode/template.yml`; every input is described in its `spec:inputs` header.

## Jobs the component adds (rules come from the inputs)

| Job | Runs on | Blocks? |
|---|---|---|
| `veracode-policy-resolve` | branches not matching `baseline_branches` | warning only (stage audit/warn) |
| `veracode-pipeline-scan` | same | by `rollout_stage` |
| `veracode-baseline` | `baseline_branches` | never |
| `veracode-policy-scan` | `release_branches`, `release_tags` | by `rollout_stage` |
| `veracode-sandbox-scan` | `sandbox_branches`, `sandbox_tags` (into sandbox `sandbox_tag_name`) | never |
| `veracode-sca` | every branch (`sca_agent`) | never |
| `veracode-cli-directory-scan` | every branch (`cli_directory_scan`) | never |
| `veracode-container-scan` | `container_branches` / `container_tags`, if `dockerfile` exists | never |

The policy and sandbox scans run in stage `.post` (input `release_stage`), so a project's own
stages never wait for the Platform. A deploy job that must follow the verdict `needs:
[veracode-policy-scan]`.

## Shapes beyond one app, one artifact (1.2.0)

| Situation | Inputs |
|---|---|
| Language without Veracode Static support (e.g. Rust) | `static_scan: false`: SCA, directory scan and container scan stay, every static job goes |
| Several applications in one repository | include the component once per application, each with its own `job_suffix` (e.g. `-console`), `app_name`, `package_job`, `artifact`, `source_dir`, `changes_paths`, `dockerfile`; job names and the baseline package carry the suffix |
| Pre-release tags (`-rc.1`, `-beta.2`) | `release_tags` anchored to final versions (`'^v\d+\.\d+\.\d+$'`), `sandbox_tags: '^v.*-(rc|beta)'`; they share one sandbox (`sandbox_tag_name`, default `prerelease`) |
| Deploy/environment branches that only receive merges | `gate_skip_branches: '^(staging|production)$'`: no gated Pipeline Scan and no baseline there; policy and sandbox scans still follow their own inputs |
| Dockerfile copies the team's build output | `container_needs: [{job: build, artifacts: true}]` (the job must run on the same refs) |
| Image is already built and pushed by the team | `container_image: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA` (pulled instead of built) |
| The policy verdict must hold a deploy | `release_stage: <a stage before the deploy stage>`, `policy_scan_timeout` > 0, `rollout_stage: block-policy`. A deploy job that uses `needs:` must list the policy scan job. Costs the wait for the Platform on every release |

Branch pipelines only: a project that runs merge-request pipelines exclusively (a `workflow:`
rule dropping branch pipelines) gets no Veracode jobs from this version.

## Rollout stages

| `rollout_stage` | Pipeline Scan on short-lived branches | Policy scan at the release point |
|---|---|---|
| `audit` (default) | reports; exit 0 whatever is found; tool errors are warnings | verdict printed; never fails |
| `warn` | flaws violating the policy (new ones when a baseline exists) → warning (exit 42, allowed) | Did Not Pass → warning |
| `block-new` | NEW policy-violating flaws vs the target branch baseline → fail; no baseline yet → warning | Did Not Pass → warning |
| `block-policy` | any policy-violating flaw → fail (no baseline) | Did Not Pass → fail |

Criteria = the policy assigned to the application profile, resolved at run time (API wrapper
`GetAppList`/`GetAppInfo`), applied with `--policy_name` (built-in policies) or
`--request_policy` + `--policy_file` (custom policies). Overrides: `policy_name`,
`fail_on_severity`.

## Include forms (same file, in order of preference)

1. Component, pinned to a release (above). Needs GitLab 17.0+.
2. Project include pinned to a tag, where components cannot be used:
   ```yaml
   include:
     - project: platform/veracode-ci
       ref: 1.3.1
       file: templates/veracode/template.yml
       inputs: { app_name: my-application-profile, sca_image: python:3.11 }
   ```
3. Last resort (the project cannot read this project, air-gapped mirror not possible): copy
   `templates/veracode/template.yml` unchanged to `.gitlab/veracode/template.yml` and
   `include: [{ local: .gitlab/veracode/template.yml, inputs: {...} }]`. The copy then has to
   be upgraded repo by repo; record why this form was needed.

Never pin to a branch or `~latest`: a release must not change under a project.

## Versions

Semantic version tags without a `v` prefix (GitLab's CI/CD Catalog accepts only `1.2.3`).
Patch = pin bumps and fixes; minor = new inputs with defaults; major = changed behaviour or
removed inputs. `VERACODE_COMPONENT_VERSION` in the template equals the tag and is printed by
every job. Pinned tool versions are input defaults at the end of `spec:inputs`;
`tools/pin-versions.sh` prints fresh values (image digests, CLI tarball SHA-256, SCA agent
SHA-256 after checking Veracode's PGP signature). See CHANGELOG.md.
