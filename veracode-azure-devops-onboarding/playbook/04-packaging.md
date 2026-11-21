# 04 Packaging by language

Veracode SAST scans the deployable, not the working tree. A wrongly packaged upload scans
"successfully" and reports almost nothing, which reads as a clean bill of health: packaging is
the step to get right and to check (module list, size, finding count plausible for the app).

The packaging job publishes one artifact (default name `veracode-package.zip`, variable
`VERACODE_ARTIFACT`); every scan job `needs:` it. Keep it separate from the team's build job
unless the team's build already produces the deployable (Java jar: reuse it).

| Language | Package | Exclude | Notes |
|---|---|---|---|
| **Python** | zip of the application package(s), entry point (`wsgi.py`, `app.py`, `manage.py`), `requirements*.txt`/`pyproject.toml`/lockfile. Serverless: the handlers (`functions/<name>/handler.py`) together with the shared package in one zip | tests, `.venv`, `__pycache__`, `.git`, data/exports, vendored third-party modules (a copied library file added 11 findings that are not the team's), deployment zips with dependencies installed into them, wheels (`.whl` is rejected: "No files found"), sdists | `python -m zipfile -c veracode-package.zip app wsgi.py requirements.txt` works in `python:*-slim` (no `zip` binary there). Verified 2026-11-11 on Flask. |
| **Java (Maven/Gradle)** | the deployable jar/war/ear the build produces (`target/*.jar`, `build/libs/*.jar`); Spring Boot fat jar is fine | test jars, sources jars | Reuse the team's artifact only if it is a debug, unobfuscated build. A release profile that sets `-g:none`, shades with relocation or runs ProGuard produces the wrong thing: add a packaging job that builds the default profile. Shaded jar: submit the UNSHADED jar plus its dependency jars (relocated libraries are counted as the team's code: 19 findings, 10 of them in relocated third-party code, vs 9). Obfuscated jar: scans SUCCESS and loses the flaws (3 findings, no command injection, no deserialization). `-g:none`: findings survive, every location is line 1. WAR with JSPs: the WAR itself. One artifact per deployable, each to its own profile when released separately. Proven 2026-11-12 on a five-module Maven reactor. No `zip` in Maven images: `jar --create --no-manifest --file x.zip -C dir .` |
| **Node / TypeScript** | zip of source (`src/`), `package.json`, lockfile, `tsconfig.json` | `node_modules`, `dist`/bundles (a minified bundle scans SUCCESS with 0 findings), vendored minified files, tests, fixtures, workspace and build-tool config (`pnpm-workspace.yaml` in the zip: 12 findings became 0; `vite.config.ts`: 7 became 1) | Veracode analyses JS/TS source. Workspace (pnpm/yarn/npm): ONE zip with the `src` of every first-party package and their `package.json` files, so flows through a shared package are followed (per-package zips lost the shared package's flaw). The agent-based SCA scan does not support pnpm (2026-11-12): directory scan is the dependency view there. `apk add zip` in `alpine:3` then `zip -qr`. Build-tool and workspace config files in the zip can change how the archive is read: the same TS source zip gave 7 findings without `vite.config.ts` and 1 with it (2026-11-12, cause unknown); zip the sources and `package.json`, then add other files only after comparing. `python -m zipfile -c` given files from several folders can flatten paths: list the archive. |
| **.NET** | **framework-dependent** publish with **PDBs**, per executable project: `dotnet publish <proj> -c Debug -p:UseAppHost=false -o out/<app>`, delete `out/<app>/runtimes/`, zip the folder. **One zip per executable** (API, worker); front-end source goes in as source, not the built bundle | tests, `runtimes/`, the apphost executable, `wwwroot` minified bundles, `bin/` and `obj/` trees | Single-file, trimmed, self-contained or ReadyToRun output is not scannable: single-file gives 0 findings or 'No files found for scanning' with SUCCESS. Release configs often set `DebugType=none`: every finding reads `UNKNOWN:1`. Native libraries under `runtimes/` are picked up as modules and the scan hangs to its timeout. Two executables in one zip: both modules are listed and the second one's findings are dropped. If publish runs an npm target, skip it for the scan build. A zip of C# source scans slowly and misses most data-flow findings. (Proven on clinic-portal, 2026-11-12.) |
| **Kotlin / JVM app with the Gradle `application` plugin** | every jar of `build/install/<app>/lib` (application jar + runtime libraries) in one zip, application jar renamed to a version-free name | test jars | `build/libs/*.jar` alone is the thin jar without libraries. Proven 2026-11-12 (Pipeline Scan, sandbox and policy scan: one module, pre-scan OK). |
| **Scala (sbt)** | the jar from `sbt package` (scalac writes debug info by default); reuse the team's job if it already runs `package` | | https://docs.veracode.com/r/compilation_scala. Proven 2026-11-12 on a library (pre-scan OK). |
| **PHP** | zip of the PHP source the application ships (`src`, `public`, `config`, `templates`) plus `composer.json`/`composer.lock` | `vendor/`, tests | Same file set as `veracode package` produces. Proven 2026-11-12 (modules "PHP files within ...", pre-scan OK); adding `vendor/` changed nothing. |
| **Ruby on Rails** (plain Ruby is not supported) | the archive written by `bundle exec veracode prepare` (Veracode's `veracode` gem, run in the app with its bundle installed and the Rails environment loadable) | | A source zip is not what Veracode analyses for Rails. Add the gem in the packaging job only (not to the team's Gemfile). Proven 2026-11-12 on Rails 6.1 / Ruby 3.0 (Pipeline Scan and policy scan, one module, pre-scan OK). https://docs.veracode.com/r/compilation_ruby |
| **Rust and other languages absent from the supported lists** | nothing | | `static_scan: false`. A compiled binary is accepted and scans green with 0 findings: that is not a result. |
| **Go** | module inside a top-level folder with `go mod vendor` output, zipped | | Go is analysed from source: release binaries and tarballs, a zip without `vendor/`, and a zip with the module files at the zip root all give "No files found for scanning". Two SILENT losses (scan green): a module pulled in through a `replace` directive (submodule, local path) is not analysed until the `replace` is removed and the vendored copy marked first-party; files behind build tags the team ships with (`-tags enterprise`) are skipped unless the tags are passed (`GOFLAGS=-tags=...` for `veracode package`). Read the Makefile for the real build flags. Upload and Scan of the auto-packaged zip passed pre-scan on 2026-11-12 (sandbox and policy), which supersedes the 2026-10 failure note. |
| **C/C++** | x86_64 ELF built `-gdwarf-2 -g3 -O0 -fno-builtin`, unstripped, zipped | | 2026-10 note, not re-verified. |
| **Containers** | the image in the docker daemon (`veracode scan --type image --source name:tag`) | | A `docker save` tarball read as an empty, clean image [PKG-01?]. Build in the scan job with dind, or pull from the registry. |

## The rule behind the table

The team's release artifact is built to run, not to be analysed, and is often the wrong thing to
scan: optimised or stripped of debug information, obfuscated, minified, bundled, trimmed, merged
with third-party code, or containing only third-party code. The engine rarely refuses such an
artifact; it scans it and reports little. So for every language:

1. Read Veracode's packaging page for the language (`https://docs.veracode.com/r/compilation_<language>`
   and the packaging cheat sheet linked from it) before choosing the artifact, and quote it in the plan.
2. Find out how the team's build differs from what that page asks for (build profiles, release
   flags, plugins that rewrite the output, builds that happen only inside `docker build`).
   If it differs, add a separate packaging job that builds what Veracode needs; never change the
   team's release build.
3. One application profile gets one package that contains every first-party module it ships,
   and nothing the team does not ship (tests, tooling, vendored copies, generated bundles).
4. Keep file names stable: the Platform identifies modules by file name, so a version number in
   the name makes every release look like a new module. Rename in the packaging job.
5. Prove it (next sections). A green scan is not proof.

## Accepted is not analysed

Four ways a wrong package looked fine on 2026-11-12, all with `SCAN_STATUS SUCCESS`:
an obfuscated jar (3 findings instead of 9), a minified bundle (0), a source zip with one extra
config file (0 instead of 12), a module behind a `replace` directive (skipped without a word).
Rules that follow:
- When Veracode's packaging page gives an instruction (remove `replace` directives, no
  obfuscation, no third-party packages, one executable per upload), follow it. "The scan
  accepted my package anyway" is not a reason to waive it; if you deviate, prove with a
  with/without comparison that nothing first-party is lost, and say so.
- Check that every first-party source location you expect is represented: list the modules or
  files the engine reports and compare with the list of things the team ships (binaries,
  submodules, build-tagged files, shared packages).
- A repository whose only supported code is incidental tooling (one helper script in an
  infrastructure repository) gets NO application profile and no static job: a profile that says
  "Pass" for 60 lines reads as a pass for the repository. Use `static_scan: false` and the
  directory scan (IaC misconfigurations, secrets), and say what is not covered.

## `veracode package` (auto-packaging)

`veracode package --source . --output veracode-package --trust` runs the language's build and
writes Veracode-ready artifacts. Use it when the manual rule is unclear (multi-language repos,
Gradle multi-module, .NET solutions). It needs the build toolchain in the image and takes
longer; its output directory may hold several files, and the Pipeline Scan takes one file per
run. Treat its output as a candidate, not as the answer (observed 2026-11-12): it exits 0 with
no artifact when the build fails; it includes tests, tools and unshipped folders; for a Maven
reactor it emitted both the shaded and the original jar; for a Python Lambda project its top
folder hid 12 of 15 findings; for .NET with a SPA it emitted the minified bundle as a JS
artifact; for Go it ignores build tags. Prune it and compare it with a hand-built package.

## Few findings: package or engine?

A plausible application with almost no findings has two possible causes, and the report must say
which one it is. Work through this before writing "N findings":

1. Name, from reading the code, three to five places where a finding is expected (a query built
   from request input, a command line, a deserialiser, a hard-coded secret).
2. Compare candidates locally with the pinned Pipeline Scan image (mind the 6 scans per minute):
   your package, the output of `veracode package` in the build image, and one deliberate
   variation (with/without dependencies, with/without a wrapping folder, debug vs release build).
   If the numbers move, the package matters: keep the variant that finds the expected places
   and say why. A variant that finds more is not automatically right (third-party code counted
   as first-party inflates it): check where the extra findings are.
3. If every reasonable package gives the same thin result, it is the engine: an unsupported
   framework (taint from HTTP requests is followed only through frameworks on the supported
   list), a library without an entry point (nothing calls its public methods, so flow-based
   flaws such as SQL injection are not reported and a policy scan can pass), or newer language
   syntax. Say "package proven, result thin", list the expected-but-missing places, and tell
   the team the scan does not cover them. Never present a thin result as a clean one.
4. For a library: say in the report that its flaws surface in the applications that call it,
   and that its own policy verdict under-reports.

## Check the package before relying on it

- List the archive in the job log (`python -m zipfile -l`, `unzip -l`, `jar tf`) and look for
  the entry point and the main package; no `node_modules`, no `.venv`, no tests.
- Size: a 2 KB zip of a web service is wrong.
- First Pipeline Scan: the module list and finding count should be plausible for the app
  (a Flask service with SQL and subprocess calls and zero findings is a packaging problem).
