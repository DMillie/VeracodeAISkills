# Veracode CLI, packaging, container/IaC scans and the SCA agent

The fastest way to see real results on one application, and the tool most
automation is built from. Sources `[v: 2026-10-09 | docs.veracode.com: Install
the Veracode CLI, veracode package, veracode static scan, veracode scan, Run
Container Security scans, About auto packaging, c_comp_quickref, SCA agent-based
scan quickstart]`.

---

## 1. Install and authenticate

**macOS / Linux**

```bash
curl -fsS https://tools.veracode.com/veracode-cli/install | sh
```

**Windows (PowerShell)**

```powershell
$ProgressPreference = "silentlyContinue"; iex ((New-Object System.Net.WebClient).DownloadString('https://tools.veracode.com/veracode-cli/install.ps1'))
```

Homebrew, Chocolatey and an MSI are also offered — use Chocolatey **or**
PowerShell on Windows, not both; use the MSI where PowerShell scripts are blocked.
Supported: macOS (Intel, or Apple silicon with Rosetta 2), Linux (Intel), Windows.
The Veracode and Veracode CLI IP ranges must be allowlisted on locked-down networks.

**Authenticate**

| Who | How |
|---|---|
| A person, organization uses SSO | `veracode auth login` |
| A person without SSO, or any automation | `veracode configure` → enter the **HMAC** API ID and key |
| CI | `VERACODE_API_KEY_ID` and `VERACODE_API_KEY_SECRET` environment variables from the CI secret store |

**It worked when** `veracode --help` lists the commands and the first scan
command gets past authentication.

## 2. Package — `veracode package`

Veracode scans **built artifacts** for most languages, and wrong packaging is the
quietest failure in the product: the scan succeeds and finds almost nothing. The
CLI's auto-packager builds the right artifact for supported stacks.

```bash
# local project; --trust is required the first time
veracode package --source . --type directory --output ./verascan --trust

# straight from a repository URL (cloned to a temp dir, then removed)
veracode package --source https://github.com/<org>/<repo> --type repo --output ./verascan --trust

# .NET, Maven, Gradle: let it detect the toolchain and write veracode.yml first
veracode package discover
```

Useful flags: `--verbose`, `--strict` (exit code 4 if a build fails during
packaging), `--exclude` (Java packages/JARs), `--skip-packagers sql,apex,cobol,perl`.

**Prerequisites:** the project must build cleanly on the machine running it, with
its compilers, build tools and package managers installed (`dotnet`/`msbuild`,
`mvn`/`gradle`, `npm`/`yarn`, `go` with `go.mod` and `go.sum`, Xcode, …).

**Auto-packaging covers:** .NET 6–10 and Framework 4.6–4.8 (MAUI, Blazor
WebAssembly) · Java via Maven/Gradle (also Kotlin, Scala/sbt) · Android (Gradle) ·
Apple (Xcode, CocoaPods) · C/C++ (GCC/Clang on Linux, MSVC) · JavaScript/TypeScript
and React Native (npm, Yarn) · Python (pip, Pipenv, setuptools, virtualenv) ·
Go 1.14–1.26 (modules) · COBOL, Dart/Flutter, Perl, PHP (Composer), PL/SQL, Ruby
on Rails (Bundler), T-SQL.

Known limits: .NET test projects are excluded; C++/CLI and C++/CX are packaged as
binaries; a Python `requirements.txt` alone packages but yields **no SCA
results** (use a lock file); the GitHub workflow integration's auto-packaging does
not cover .NET.

### Packaging by hand — the rules that matter

| Language | Submit |
|---|---|
| Java | JAR, WAR or EAR **compiled with debug symbols** |
| .NET | ZIP of a **debug** build including the `deps.json` files; ASP.NET from the published directory |
| JavaScript / TypeScript | Source as a ZIP; **no test code or built `dist` files**; remove `node_modules` if lock files are present |
| Python | Source ZIP with `Pipfile.lock` at the root |
| PHP | Source ZIP with `composer.lock` at the root |
| Android | Debug build as an APK |
| C/C++ (Linux, GCC) | Debug build with `-gdwarf-2 -g3 -O0 -fno-builtin` |
| C/C++ (Windows) | Debug build with `/Zi /Od /GS- /MTd /link /INCREMENTAL:NO /DEBUG:FULL` |

For anything else, point at Veracode's packaging guidance for that language
rather than guessing — `docs.veracode.com/r/compilation_packaging`.

## 3. Scan

### Fast local SAST feedback — `veracode static scan`

```bash
veracode static scan ./verascan/<artifact>.zip --fail-on-severity "Very High, High" \
  --results-file results.json --summary-output summary.txt
```

This is a **Pipeline Scan**: results come back in minutes and **stay local**
(`results.json`). Nothing appears in the Platform and the compliance verdict is
untouched. Exit code 3 means flaws matched the fail criteria. Use
`--baseline-file results.json` on later runs to report only new flaws.

### Results in the Platform

Upload the packaged artifact to an application profile — by hand the first time
(`platform-setup.md` §7), then from CI (`ci-pipelines.md`). That is a **policy
scan** (or a sandbox scan, if a sandbox is chosen) and is what the compliance
verdict and every report use.

### Containers, IaC and secrets — `veracode scan` (Container Security)

```bash
veracode scan --source alpine:latest --type image                     # a container image
veracode scan --source ./ --type directory                            # IaC + secrets in a directory
veracode scan --source https://github.com/<org>/<repo> --type repo    # a remote repository
veracode scan --source <...> --type <...> --format json --output results.json
```

`--type`: `image`, `directory`, `repo`, `archive`. `--format`: `table`, `json`
(Syft schema), `cyclonedx` (CycloneDX 1.6 XML — an SBOM). Add a policy with
`veracode policy get <name>` then `--policy <file>.rego`. IaC coverage includes
Kubernetes, Dockerfiles, Terraform, CloudFormation and Helm. Results print to the
terminal or a file; plan to keep them as a CI artifact.

## 4. SCA agent-based scanning

The agent scans a repository's **dependencies from source**, before any build
artifact exists. It organises results by **workspace and project**, not by
application profile (a project can be linked to a profile afterwards). It needs
an SCA subscription and a **UI user** with Workspace Administrator or Editor,
Security Lead and Submitter.

1. **Scans & Analysis** → **Software Composition Analysis** → **Agent-Based Scan**
   tab → **My Workspace** (or a workspace per team).
2. **Agents** → **Actions** → **Create** → choose the OS. The page shows the
   install commands and an **activation token**; store the token like a secret.
3. Install with the commands shown, authenticate (activation token, or OAuth for
   SSO users, or HMAC for automation), then check with `srcclr test`.
4. Scan:

   ```bash
   srcclr scan --update-advisor --url https://github.com/<org>/<repo>
   srcclr scan /path/to/project
   ```

   Results print and upload to the workspace unless `--no-upload` is given.
5. Review under **Software Composition Analysis** → **Agent-Based Scan** → the
   workspace: Issues, Projects, Vulnerabilities, Libraries, Licenses.

In the repository-scanning integrations this is what `VERACODE_AGENT_TOKEN` /
SRCCLR API TOKEN is for. EU accounts sign in at `analysiscenter.veracode.eu`, and
the GitHub integration sets `SRCCLR_REGION: ER`.

**Upload-based SCA** is different: it runs as part of a policy or sandbox scan of
the uploaded artifact and reports in the application profile. Customers often
have both; make sure they know which results they are looking at.

---

## Where it goes wrong

| Symptom | Usual cause |
|---|---|
| Scan finishes with almost no findings | Packaging: tests or `dist` included, no debug symbols, wrong module selected, lock files missing |
| `veracode package` fails | The project does not build on that machine, or a build tool is missing from `PATH` |
| Python app has no SCA results | Only `requirements.txt`; add a lock file (`Pipfile.lock`) |
| `veracode static scan` passed but the Platform shows nothing | Expected: it is a Pipeline Scan. Upload to a profile for Platform results |
| Agent scan uploaded, application profile shows no SCA | Agent results live in the workspace until the project is linked to the profile |
| CLI or agent cannot connect from the corporate network | IP allowlisting, or a proxy |
| Apple silicon Mac: CLI will not run | Rosetta 2 not installed |
