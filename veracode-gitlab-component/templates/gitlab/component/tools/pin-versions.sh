#!/usr/bin/env bash
# Print the values for the pinned-version inputs of templates/veracode/template.yml.
#   usage: pin-versions.sh [--cli VERSION] [--sca VERSION] [--pipeline-scan TAG] [--api-wrapper TAG]
# Defaults: the vendor's current versions (LATEST_VERSION files, `latest` image tags are only
# READ here to learn the version; nothing unpinned ends up in the component).
# Needs docker, curl, sha256sum; gpg for the SCA agent signature (Veracode signs the agent
# archive; it publishes no checksum for the CLI, so that SHA-256 is trust-on-first-use).
set -euo pipefail
SCA_KEY_FPR="2B93609DA5A49D7F2082246FDF7DD7A50B746DD4"   # "Production (Official Key) <production@srcclr.com>", seen 2026-11-12
CLI=""; SCA=""; PS=""; AW=""
while [ $# -gt 0 ]; do case "$1" in --cli) CLI="$2"; shift;; --sca) SCA="$2"; shift;; --pipeline-scan) PS="$2"; shift;; --api-wrapper) AW="$2"; shift;; *) echo "unknown $1" >&2; exit 2;; esac; shift; done
W="$(mktemp -d)"; trap 'rm -rf "${W:?}"' EXIT
[ -n "$CLI" ] || CLI="$(curl -fsS https://tools.veracode.com/veracode-cli/LATEST_VERSION)"
[ -n "$SCA" ] || SCA="$(curl -fsS https://sca-downloads.veracode.com/LATEST_VERSION)"
curl -fsSL -o "$W/cli.tgz" "https://tools.veracode.com/veracode-cli/veracode-cli_${CLI}_linux_x86.tar.gz"
echo "cli_version: '$CLI'"
echo "cli_sha256: '$(sha256sum "$W/cli.tgz" | cut -d' ' -f1)'   # no vendor checksum: trust on first use"
if command -v gpg >/dev/null; then
  export GNUPGHOME="$W/gnupg"; mkdir -m 700 "$GNUPGHOME"
  curl -fsSL https://sca-downloads.veracode.com/redhat/SRCCLR-GPG-KEY | gpg -q --import 2>/dev/null
  gpg --list-keys --with-colons | grep -q "^fpr:.*:$SCA_KEY_FPR:" || { echo "ERROR: the SCA signing key fingerprint changed; investigate before pinning" >&2; exit 1; }
fi
echo "sca_agent_version: '$SCA'"
for os in linux:glibc linux_musl_x64:musl; do
  f="srcclr-$SCA-${os%%:*}.tgz"; curl -fsSL -o "$W/$f" "https://sca-downloads.veracode.com/$f"
  sig="not checked (no gpg)"
  if command -v gpg >/dev/null; then
    if curl -fsSL -o "$W/$f.asc" "https://sca-downloads.veracode.com/$f.asc" && gpg --verify "$W/$f.asc" "$W/$f" 2>/dev/null; then sig="PGP signature good ($SCA_KEY_FPR)"; else echo "ERROR: PGP verification failed for $f" >&2; exit 1; fi
  fi
  echo "sca_agent_sha256_${os##*:}: '$(sha256sum "$W/$f" | cut -d' ' -f1)'   # $sig"
done
pin() { # image repo, tag (empty = read the version label of latest is not reliable: require a tag)
  docker pull -q "$1:$2" >/dev/null; echo "$1:$2@$(docker inspect --format '{{index .RepoDigests 0}}' "$1:$2" | cut -d@ -f2)"; }
[ -n "$PS" ] && echo "pipeline_scan_image: '$(pin veracode/pipeline-scan "$PS")'"
[ -n "$AW" ] && echo "api_wrapper_image: '$(pin veracode/api-wrapper-java "$AW")'"
[ -n "$PS$AW" ] || echo "# images: pass --pipeline-scan TAG / --api-wrapper TAG (version tags: hub.docker.com/r/veracode/pipeline-scan/tags)"
