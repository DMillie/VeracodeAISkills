# Tools and images

- `veracode/pipeline-scan` (pinned `26.11.0@sha256:…` in the component): Alpine, OpenJDK 11, jar at
  `/opt/veracode/pipeline-scan.jar`; `curl`, `wget`, `zip`, `unzip` present. [IMG-01]
- `veracode/api-wrapper-java` (pinned `26.10.20.1@sha256:…`): Alpine, jar at
  `/opt/veracode/api-wrapper.jar` (`-action UploadAndScan` etc.); `curl` present. [IMG-02]
- Both images run as **uid 1000**. A GitLab Runner docker executor reuses a build volume per
  concurrency slot; after a root-image job created the checkout, a job in these images cannot
  write `results.json` ("Permission denied", intermittent). The component runs these jobs with
  `image:docker:user: root`. [IMG-03]
- There is no official `veracode/veracode-cli` image (pull denied). The component downloads
  `veracode-cli_<version>_linux_x86.tar.gz` and checks its SHA-256 instead of piping Veracode's
  install script into a shell. That script writes `./veracode` into the **current directory**:
  install outside the tree you will scan, or a directory scan reports the CLI's own Go modules.
  [IMG-04]
- SCA agent: the component downloads `srcclr-<version>-linux[_musl_x64].tgz`, checks the SHA-256
  and runs `bin/srcclr scan`; it does not execute `ci.sh` (which verifies nothing). The image
  needs `curl` and the project's package manager. [IMG-05]
- All four tools are x86_64-only; on arm64 runners use `amd64/` images with platform
  `linux/amd64`. A multi-arch tag pulled for arm64 can break the next amd64 pull on a shared
  daemon. [IMG-06?]
- Under emulation the CLI's credential check can time out and still exit 0: check output files,
  not exit codes. [IMG-07?]

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
