# 6. Direct downloads: pipeline-scan zip and Java API wrapper

| Fact | Source | Marker |
|---|---|---|
| `pipeline-scan-LATEST.zip` reachable; Last-Modified 2026-11-10, 7,880,891 bytes (same size as the 26.11.0 zip). | https://downloads.veracode.com/securityscan/pipeline-scan-LATEST.zip | observed (2026-11-12) |
| Versioned zips exist (HTTP 200): `pipeline-scan-26.11.0.zip`, `-26.9.0.zip`, `-26.7.0.zip`, `-25.8.2.zip`, `-22.9.0.zip`. The pattern is not documented; docs only reference LATEST and recommend the Docker image. | https://downloads.veracode.com/securityscan/pipeline-scan-26.11.0.zip | observed (2026-11-12) |
| No checksum file found (`pipeline-scan-LATEST.zip.sha256` returns 404). | same host | observed (2026-11-12) |
| Docs recommend fetching LATEST on every run or caching it; this conflicts with version pinning, so pinning is our decision, not vendor guidance. | https://docs.veracode.com/r/Pipeline_Scan | docs only (read 2026-11-12) |
| Java API wrapper on Maven Central `com.veracode.vosp.api.wrappers:vosp-api-wrappers-java`: latest and release = **26.10.20.1**; previous: 26.10.20.0, 26.3.19.0, 26.2.18.0, 25.11.17.0, 25.8.16.1. Maven Central serves `.sha1`/`.md5` (and normally `.asc`) per artifact. | https://repo1.maven.org/maven2/com/veracode/vosp/api/wrappers/vosp-api-wrappers-java/maven-metadata.xml | observed (2026-11-12) |
| Docker tags 26.3.19.0.1 / .0.2 exist for the wrapper image without a matching Maven version (image rebuilds). | Docker Hub API vs Maven metadata | observed (2026-11-12) |
| Jar inside the zip matches the Docker image version; zip SHA-256 recorded by us | - | not verified locally (the component uses the Docker image, not the zip) |

Index and reading guide: `reference/integration-options.md`.
