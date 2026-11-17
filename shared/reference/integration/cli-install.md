# 4. Veracode CLI: installing a specific version

| Fact | Source | Marker |
|---|---|---|
| Latest version: `LATEST_VERSION` returns **2.55.0**; release notes show v2.55.0 dated November 5, 2026 (v2.54.1 Oct 27, v2.54.0 Oct 23, v2.53.0 Oct 13). | https://tools.veracode.com/veracode-cli/LATEST_VERSION ; https://docs.veracode.com/updates/r/Veracode_CLI_Updates | observed / docs only (read 2026-11-12) |
| Documented pin: `curl -fsS https://tools.veracode.com/veracode-cli/install \| VERACODE_CLI_VERSION=<version> sh`. Veracode recommends always using the latest. | https://docs.veracode.com/r/Install_a_specific_version_of_the_CLI | docs only (read 2026-11-12) |
| Install script honours `VERACODE_CLI_VERSION` (else reads `LATEST_VERSION`) and `VERACODE_CLI_DOWNLOAD_URL` (alternate base URL, e.g. an internal mirror). | https://tools.veracode.com/veracode-cli/install | docs only (read 2026-11-12) |
| Download pattern used by the script: `https://tools.veracode.com/veracode-cli/veracode-cli_<version>_<suffix>.tar.gz`, suffix `linux_x86`, `macosx_x86` or `macosx_arm64`. Linux is x86_64 only. | same | docs only (read 2026-11-12) |
| The script pipes the tarball straight into `tar` and runs the bundled `install.sh`. It performs **no checksum or signature verification**. | same | docs only (read 2026-11-12) |
| No checksum/signature files found: `.sha256`, `.sig`, `.asc`, `checksums.txt` next to the 2.55.0 tarball all return 404. Published checksums: **not confirmed** (none found). | https://tools.veracode.com/veracode-cli/veracode-cli_2.55.0_linux_x86.tar.gz.sha256 (404) | observed (2026-11-12) |
| Versioned tarballs reachable (HTTP 200): 2.55.0, 2.54.0, 2.53.0, 2.52.0, 2.51.0, 2.50.0, 2.45.0. 2.40.0 and 2.35.0 return 404, so old versions are removed; a pin needs an internal mirror to stay reproducible. | https://tools.veracode.com/veracode-cli/veracode-cli_2.55.0_linux_x86.tar.gz | observed (2026-11-12) |
| Other channels: Homebrew `veracode-cli@<version>` (at most four versions behind latest), Chocolatey `--version`, signed Windows MSI, PowerShell `install.ps1` taking a version argument. | https://docs.veracode.com/r/Install_a_specific_version_of_the_CLI | docs only (read 2026-11-12) |
| No official Veracode CLI Docker image on Docker Hub (`veracode/veracode-cli` not found). | https://hub.docker.com/v2/repositories/veracode/ | observed (2026-11-12) |
| Self-computed SHA-256 of the pinned tarball, recorded by us | - | verified locally 2026-11-12 (`reference/integration/verified-locally.md`) |

Index and reading guide: `reference/integration-options.md`.
