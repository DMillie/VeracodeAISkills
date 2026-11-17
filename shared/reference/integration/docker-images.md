# 3. Docker Hub images (namespace `veracode`)

Repositories listed by the Docker Hub API (7): `pipeline-scan`, `api-wrapper-java`, `scm-packaging`, `api-signing`, `vrm-runtime-agent`, `vulnerable-verademo-java`, `vulnerable-verademo-dotnet`. `veracode/veracode-cli` and `veracode/scm-integration` returned "object not found". No SCA agent (srcclr) image exists in this namespace.
Source: https://hub.docker.com/v2/repositories/veracode/?page_size=100 - observed (2026-11-12).

Digests below are the tag digests reported by the Docker Hub API (amd64). Verify with `docker pull <repo>@<digest>` before pinning: **verified locally 2026-11-12** for the four pinned images (`reference/integration/verified-locally.md`).

`veracode/pipeline-scan` (168 tags; each version has `X.Y.Z` and `cmd-X.Y.Z`; floating `latest` and `cmd`). Source: https://hub.docker.com/v2/repositories/veracode/pipeline-scan/tags?page_size=25

| Tag | Pushed | Digest | Marker |
|---|---|---|---|
| 26.11.0 (= latest) | 2026-11-10 | sha256:bde005b807ceb2f6f0439f5f0fa79a5fdcb0284abc9cf8d0919a3fafffce9a6b | observed (2026-11-12) |
| cmd-26.11.0 (= cmd) | 2026-11-10 | sha256:931cff70ad1bb0a8a8000b2c24a6645bf50a38ef2b714bc1faf567b7a1a6c0d6 | observed (2026-11-12) |
| 26.9.0 | 2026-09-23 | sha256:65d29e457b16e25e535658e40405dda6e19895576e19aad13fd5d930566bcf83 | observed (2026-11-12) |
| cmd-26.9.0 | 2026-09-23 | sha256:894fd6d68bb2b2177f1a6931806be426e547ec627a5e750e3d938b23752676da | observed (2026-11-12) |
| 26.7.0 | 2026-07-29 | sha256:282f1effbebd07a26a025ce364803bed755b90cc5066284791c5064320c25abf (index) | observed (2026-11-12) |
| 26.3.0 | 2026-03-02 | sha256:e896c7b21dc542ca7bf9e1924defb3f39cdd062dc26e1ed29a95ed150cc6fd92 (index) | observed (2026-11-12) |
| 26.2.1 | 2026-02-23 | sha256:6323606a7f50f87e8f435b13e248967f21370ac8b65032627a7f92fcfbe7bf62 (index) | observed (2026-11-12) |
| 25.8.2 | 2025-09-15 | sha256:029aaeb459a05273c83bfa9d106ff7a212967756879b941455413ea66869a5e2 | observed (2026-11-12) |

Older tags seen: 26.2.0, 25.8.1, 25.8.0, 25.7.1, 25.7.0, 25.2.0. 26.11.0 was pushed two days before this snapshot; consider 26.9.0 if a soak period is wanted. Difference between plain and `cmd-` variants (entrypoint) is **not confirmed**: local verification: TODO.

`veracode/api-wrapper-java` (90 tags; same `X` / `cmd-X` scheme). Source: https://hub.docker.com/v2/repositories/veracode/api-wrapper-java/tags?page_size=25

| Tag | Pushed | Digest | Marker |
|---|---|---|---|
| 26.10.20.1 (= latest) | 2026-10-09 | sha256:cfdb8ea641a0b5b160afc3920d1995deeb722fb902b5c5e79cf6a711cc56ca11 | observed (2026-11-12) |
| cmd-26.10.20.1 (= cmd) | 2026-10-09 | sha256:533b97a187f9706e46009eeb67cacd9afea2f02126ffc871e2515843eec6aa2a | observed (2026-11-12) |
| 26.10.20.0 | 2026-10-07 | sha256:df6a9e01cd30f478129e6edcd2275b3f911c378977aa396506c9e8a3c6aed817 | observed (2026-11-12) |
| 26.3.19.0.2 | 2026-09-11 | sha256:4838b7454deb9f96a26d808e214a1171195bf3234a62ee4c7dea4d2dce4659a1 | observed (2026-11-12) |
| 26.3.19.0 | 2026-03-18 | sha256:89b744a72313159aef6711c3a5c8a88358dc21649050651ed23be97448b7f3c7 (index) | observed (2026-11-12) |
| 26.2.18.0 | 2026-02-10 | sha256:75b70c2b0e47c3e16548c29e648f18b5eaa65b58d0142977f221b9980e1361bc (index) | observed (2026-11-12) |
| 25.11.17.0 | 2025-11-18 | sha256:53b1c780e9a764cb7682fa2a65f73a8b87b32040a235352811c4a23d2dfbdf50 | observed (2026-11-12) |

`veracode/scm-packaging` (8 tags; image used by Repository Scanning and by the catalog components): 5.0.0 (= latest, 2026-07-30) sha256:a03dec89dbf36e5db3a563a27f6ff01343793c94c137f920ca2e8fe6d517e3de; 4.0.0 (2026-04-27) sha256:e30400cae51641530c54e437374e63f04469c90335b5d5a9b92533e9c1569d9a; 3.0.0, 2.1.0, 2.0.0, 1.0.1, 1.0.0. Source: https://hub.docker.com/v2/repositories/veracode/scm-packaging/tags - observed (2026-11-12).

Index and reading guide: `reference/integration-options.md`.
