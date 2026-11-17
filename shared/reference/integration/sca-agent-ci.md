# 5. SCA agent in CI

| Fact | Source | Marker |
|---|---|---|
| Documented GitLab step: add `curl -sSL https://sca-downloads.veracode.com/ci.sh \| sh` (docs place it in `after_script`); token in masked CI variable `SRCCLR_API_TOKEN`. Agent type is created as "Bitbucket Pipelines" in the Platform; GitLab mirrors that flow. | https://docs.veracode.com/r/Integrate_agents_with_GitLab | docs only (read 2026-11-12) |
| `https://download.sourceclear.com/ci.sh` and `https://sca-downloads.veracode.com/ci.sh` are byte-identical (same SHA-256 on fetch; Last-Modified 2024-12-17). Current docs use the veracode.com host. | both URLs | observed (2026-11-12) |
| ci.sh downloads `https://sca-downloads.veracode.com/srcclr-<version>-<os>.tgz` where os is `linux`, `linux_musl_x64` (Alpine) or `macosx`; x86_64 only on Linux. Version comes from `https://sca-downloads.veracode.com/LATEST_VERSION` unless overridden. | https://sca-downloads.veracode.com/ci.sh | docs only (read 2026-11-12) |
| ci.sh honours env var `SRCCLR_VERSION` to pin the agent version. This variable is in the script but **not in the docs** pages read. | script; https://docs.veracode.com/r/Integrate_SCA_agents | docs only (read 2026-11-12) |
| Other env vars (documented): `DEBUG`, `NOCACHE`, `CACHE_DIR` (default `/tmp`), `NOSCAN`, `SCAN_DIR`, `SRCCLR_CI_JSON`, `VERBOSE`, `CUSTOM_JRE_DIR`. Custom agent commands: `... \| sh -s -- scan ...`. Default command: `scan --allow-dirty`. | https://docs.veracode.com/r/Integrate_SCA_agents | docs only (read 2026-11-12) |
| ci.sh performs **no checksum or signature verification** of the tgz; it extracts and `exec`s `srcclr`. If `LATEST_VERSION` cannot be fetched it falls back to version "latest". | script | docs only (read 2026-11-12) |
| Latest agent version: **3.8.125** (`LATEST_VERSION`). Versioned tgz reachable: `srcclr-3.8.125-linux.tgz` (200), `srcclr-3.8.100-linux.tgz` (200), `srcclr-latest-linux.tgz` (200). | https://sca-downloads.veracode.com/LATEST_VERSION | observed (2026-11-12) |
| A detached PGP signature exists: `srcclr-3.8.125-linux.tgz.asc` (200). `.sha256` and `.sig` return 403. Which public key verifies it is **not confirmed**; the yum repo config in docs references `https://sca-downloads.veracode.com/redhat/SRCCLR-GPG-KEY`. | https://sca-downloads.veracode.com/srcclr-3.8.125-linux.tgz.asc ; https://docs.veracode.com/r/Set_up_SCA_agents | observed (2026-11-12) |
| Package-manager installs (apt-get, yum with `gpgcheck=1`, Homebrew, PowerShell `ci.ps1`) are documented as alternatives. | https://docs.veracode.com/r/Set_up_SCA_agents | docs only (read 2026-11-12) |
| Official SCA agent Docker image: none in the `veracode` Docker Hub namespace; none found in docs. | https://hub.docker.com/v2/repositories/veracode/ | not confirmed (none found) |
| `gpg --verify` of the .asc against the vendor key; `SRCCLR_VERSION` pin behaviour | - | verified locally 2026-11-12: signature good (`evidence/verified-locally-2026-11-12.md` in the source repository); `SRCCLR_VERSION` not exercised (the component does not run ci.sh) |

Index and reading guide: `reference/integration-options.md`.
