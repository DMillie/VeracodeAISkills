# Bitbucket Cloud facts that matter here

Read in Atlassian's and Veracode's documentation on 2026-11-18, except where marked. **Nothing in
this file has been run on Bitbucket.** Treat the template as a draft until one pipeline has run.

- The example's package, Pipeline Scan and report step scripts, run locally in their pinned
  images against the TypeScript sample, gave the proven count (12) and a 12-annotation Code
  Insights payload. That proves the scripts, not Bitbucket's runners or its report API. [BB-16]

## Cost and capacity
- Build minutes are a monthly allowance per workspace: Free 50, Standard 2,500, Premium 3,500;
  a 2x step counts double, 4x four times. Self-hosted runners use none. [BB-01~]
- A step that waits for a Veracode policy scan burns minutes for the whole wait. On Bitbucket's
  own runners submit the release-point scan and do not wait (`-scantimeout` unset); read the
  verdict from the Platform or a later, manual pipeline. [BB-02~]
- A step has 4 GB shared between the script and its services; the docker service takes 1 GB by
  default. Step `max-time` defaults to 120 minutes. [BB-03~]

## Reuse across repositories
- There is no Veracode pipe in Atlassian's official pipes catalog, no Veracode app for Bitbucket
  pipelines in the Marketplace, and no Bitbucket example for Pipeline Scan in Veracode's
  documentation. Veracode's only Bitbucket page covers the agent-based SCA scan. Integration is
  rung 3 (pinned tools called from the pipeline) unless the organisation builds its own pipe. [BB-04~]
- Sharing pipeline configuration (`export: true` in the source repository, `definitions:
  imports:` plus `import: <pipeline>@<alias>` in the consumer) is Premium only, stays inside one
  workspace, and imports **whole pipelines**, not steps. It cannot add steps to a team's existing
  pipeline. A branch import follows the branch head; import a tag. Variables come from the
  importing repository. [BB-05~]
- A custom pipe (`pipe: docker://<account>/<image>:<version>`) is the step-level reusable unit.
  It needs an image registry Bitbucket's runners can pull from. Pin the version; digest pinning
  for pipes is not documented. [BB-06~]
- Dynamic Pipelines (Premium, a Forge app that rewrites the configuration at run time, also
  workspace-wide) can inject steps into every pipeline. It is an app to build and operate, not a
  setting. [BB-07~]

## Triggers and variables
- `pull-requests` pipelines run on the source branch with the destination merged in, and run **in
  addition to** a matching `branches` or `default` pipeline: overlapping definitions run two
  pipelines and pay twice. Pull requests from forks do not trigger pipelines. [BB-08~]
- Variable precedence: pipeline run > deployment > repository > workspace. Workspace variables
  need a workspace admin and suit the Veracode credentials; secured variables are masked and
  cannot be read back. Names used here: `VERACODE_API_KEY_ID`, `VERACODE_API_KEY_SECRET`,
  `SRCCLR_API_TOKEN`. [BB-09~]
- Artifacts declared by a step are downloaded by later steps and kept 14 days. Steps inside one
  `parallel` group do not see each other's artifacts. [BB-10~]

## Showing results in Bitbucket
- Code Insights: `PUT /2.0/repositories/{workspace}/{repo}/commit/{commit}/reports/{id}` creates a
  report; annotations are posted in batches of at most 100, 1,000 per report. Inside a step the
  request goes through the proxy `http://localhost:29418` to `http://api.bitbucket.org/...`
  (plain http) and gets its authorisation added; no token is needed. [BB-11~]
- Requiring a green build before merge is a merge check that is only **enforced** on Premium;
  on other plans it is a warning and the merge still goes through. [BB-12~]

## Access for whoever sets this up
- App passwords were removed on 2026-07-28. REST calls use an Atlassian API token **created with
  Bitbucket scopes**, as Basic `email:token`. An unscoped Atlassian token is rejected with 401
  "Token is invalid, expired, or not supported for this endpoint". [BB-13~]
- Creating a repository and enabling Pipelines need the repository admin scope; writing pipeline
  variables needs the pipeline variable scope. [BB-14~]
- Veracode SCA agent in a step: Veracode documents `curl -sSL
  https://sca-downloads.veracode.com/ci.sh | sh` with a secured `SRCCLR_API_TOKEN` and an agent of
  type "Bitbucket Pipelines". This pack does not pipe a download into a shell: use the pinned,
  checksum-verified agent as on GitLab. [BB-15~]

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
