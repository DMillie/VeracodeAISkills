# Veracode CLI (2.55.0)

- `veracode scan --type directory --source . --format table --output file.txt` writes the table
  to the file and only INF lines to stdout; `cat` the file in CI. Uses the HMAC credentials from
  `VERACODE_API_KEY_ID/SECRET`; no agent token. On a Flask 1.1.2 app it reported 40 rows
  (CRITICAL..MEDIUM) from the pinned requirements. **[live 2026-11-11]**
- `veracode scan --type image --source name:tag` scans from the docker daemon; a `docker save`
  tarball read as empty and clean. **[2026-10]**
- The CLI ignored `~/.veracode/credentials` in the documented `[default]` ini form and said
  "credentials undefined"; it works with the two environment variables exported. **[live 2026-11-11]**
- `veracode static scan` (Pipeline Scan through the CLI) uses hyphenated flags
  (`--fail-on-severity`, `--baseline-file`, `--results-file`); exit 3 on matching flaws.

## `veracode scan static` (local scan, results stay on the machine)

- `veracode scan static <path>` packages and scans a git checkout; `veracode findings static list
  <path> --json` exports the cached findings. These scans do not appear in the Platform.
  **[live 2026-11-17, CLI 2.55.0, one repository]**
- On a pnpm workspace it built four artifacts (workspace root plus one per package) and reported
  `SUCCESS`, 22 findings. 12 is correct: the per-package artifacts repeat 10 findings under
  shorter paths (`src/...` instead of `packages/api/src/...`) and miss the two that cross
  packages. Group by artifact and remove repeats before quoting a count. **[live 2026-11-17]**
- The packager warned that the npm build failed for two packages and still exited successfully.
  **[live 2026-11-17]**
- The checkout needs a URL-style `origin` remote; with a local-path remote the scan stops after
  packaging with `invalid asset name format: unknown`. **[live 2026-11-17]**

Tags: **[live <date>]** observed in the lab on that date; **[2026-10, not re-verified]** carried over, check before relying on it.
