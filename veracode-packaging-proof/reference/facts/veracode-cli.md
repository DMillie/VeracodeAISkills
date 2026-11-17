# Veracode CLI (2.55.0)

- Credentials: export `VERACODE_API_KEY_ID` / `VERACODE_API_KEY_SECRET` (the HMAC pair). The
  `~/.veracode/credentials` file is not read ("credentials undefined"). No agent token. [CLI-03]
- `veracode scan --type directory --source . --format table --output file.txt` writes the table
  to the file and only INF lines to stdout: `cat` the file in CI. [CLI-01]
- `veracode scan --type image --source name:tag` scans from the docker daemon. A `docker save`
  tarball reads as empty and clean: never scan a tarball. [CLI-02?]
- `veracode static scan` (Pipeline Scan through the CLI) uses hyphenated flags
  (`--fail-on-severity`, `--baseline-file`, `--results-file`); exit 3 on matching flaws.

## `veracode scan static` (local scan, results stay on the machine)

- `veracode scan static <path>` packages and scans a git checkout; `veracode findings static list
  <path> --json` exports the cached findings. These scans do not appear in the Platform. [CLI-04]
- On a multi-package workspace it builds one artifact for the root and one per package and
  reports the sum. The per-package artifacts repeat root findings under shorter paths and miss
  flows that cross packages. Group findings by artifact and remove repeats before quoting a
  count. [CLI-05]
- The packager can warn that a package's build failed and still exit successfully: read the
  warnings, not the exit code. [CLI-06]
- The checkout needs a URL-style `origin` remote; with a local-path remote the scan stops after
  packaging with `invalid asset name format: unknown`. [CLI-07]

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
