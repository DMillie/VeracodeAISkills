---
name: veracode-packaging-proof
description: Build the right artifact for Veracode static analysis and prove it is right, or diagnose a scan that came back green with few or no findings. Use when packaging an app for Veracode (Java, Kotlin, Scala, .NET, Python, Go, Node or TypeScript, PHP, Rails), when a Pipeline Scan or policy scan reports zero or suspiciously few findings, when findings show UNKNOWN file or line 1, when a scan hangs or a module is missing, or when deciding whether a thin result is a packaging problem or an engine limit.
---

# Veracode packaging: build it, then prove it

Veracode static analysis scans the deployable, not the working tree. A wrong package almost never
fails. It scans, returns `SUCCESS` and reports little, which reads as a clean bill of health. So
packaging has two halves: choose the artifact, then prove it.

## 1. Choose the artifact

Read the row for the stack in `playbook/04-packaging.md`, then Veracode's own packaging page for
the language (`https://docs.veracode.com/r/compilation_<language>`), and quote it in your plan.

The rule behind every row: the team's release artifact is built to run, not to be analysed. Expect
it to be optimised, stripped, obfuscated, minified, bundled, trimmed or merged with third-party
code. When it is, add a separate packaging job that builds what Veracode needs. Never change the
team's release build.

- One application profile gets one package holding every first-party module it ships and nothing
  it does not ship (tests, tooling, vendored copies, generated bundles).
- Keep file names stable: a version number in the name makes each release a new module.
- When the packaging page gives an instruction, follow it. An accepted scan is not a waiver.

## 2. Prove it

1. From reading the code, name three to five places where a finding is expected.
2. Scan candidates locally with the Pipeline Scan (limit: 6 submissions per minute per API user):
   your package, the output of `veracode package`, and one deliberate variation (with or without
   dependencies, with or without a wrapping folder, debug or release build).
3. Check each result:
   `node tools/scan-check.js results.json --module <deployable> --place <file>`
   It flags an ignored deployable, zero findings, missing debug information, third-party or test
   code, two executables in one upload, and expected places with no finding. Use `results.json`,
   not `filtered_results.json`, where zero is normal.
4. If the numbers move between candidates, the package matters: keep the variant that finds the
   expected places and say why. More findings is not automatically better: check where they are.
5. If every reasonable package gives the same thin result, it is the engine: an unsupported
   framework, a library with no entry point, or newer syntax. Report "package proven, result thin",
   list the expected places that are missing, and tell the team the scan does not cover them.

Never present a thin result as a clean one.

## Traps seen in testing (all returned SUCCESS)

| Stack | Wrong package | What happened |
|---|---|---|
| Java | obfuscated, shaded release jar | 3 findings instead of 9; the command injection disappeared |
| Java | release profile without debug info | findings with no file or line |
| TypeScript, pnpm | source zip that includes `pnpm-workspace.yaml` | 0 findings instead of 12 |
| Node front end | minified bundle without source map | 0 findings |
| Python Lambda | `veracode package` output as produced | 3 findings instead of 15 |
| .NET | single-file, trimmed, self-contained publish | executable ignored; 0 findings |
| .NET | publish output with `runtimes/` | native library picked as a module; scan hangs to its timeout |
| .NET | API and worker in one zip | both modules listed; the worker's findings dropped |
| .NET | zip of C# source | scans slowly, misses most data-flow findings |
| Go | module behind a `replace` directive | that code silently unscanned (17 of 20) |
| Go | default build with build-tagged files | tagged file not analysed |
| Scala library | correct jar, no entry point | policy Pass with two SQL injections in the code |
| Rust | debug binary | accepted, SUCCESS, 0 findings: the language is not analysed |

`veracode package` is a candidate, not the answer: it exits 0 with no artifact when the build
fails, includes tests and tools, emits both shaded and original jars, and ignores Go build tags.

## With the Veracode CLI local scan

`veracode scan static <path>` packages and scans a checkout and keeps the results on the machine.
Tested on one repository: it reported `SUCCESS` with 22 findings where 12 is correct, because it
scans the workspace root and each package separately and the same findings come back under
different paths. Group by artifact and remove repeats before quoting a count. Details and the
other quirks are in `reference/facts/veracode-cli.md`. These scans prove a package; they do not
appear in the Platform and do not replace pipeline scans.

The proof method is the same with any scanner: compare candidates and check where the findings
land. Stop when one candidate is chosen and the counts for every candidate are written down. Do
not fix findings from this skill.

## Reading the Platform's answer

For sandbox and policy scans, read the pre-scan module list back from the Platform and compare it
with what the team ships. "Accepted upload" is not "completed scan". A policy verdict can be
decided by library findings in the upload rather than static flaws: say which.
`reference/troubleshooting.md` maps symptoms to causes; `reference/facts/pipeline-scan.md`,
`reference/facts/upload-and-scan.md` and `reference/facts/veracode-cli.md` hold dated
observed behaviour.
