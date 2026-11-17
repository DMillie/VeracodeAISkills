# Evidence register: UPL

| ID | Basis | Checked | Source or observation | Claim as written in the skill | File |
|---|---|---|---|---|---|
| UPL-01 | lab | 2026-11-11 | -help | `-action UploadAndScan -vid -vkey -appname -createprofile {true,false} -filepath -version -autoscan true -deleteincompletescan 1 [-scantimeout minutes] [-sandboxname -createsandbox true]`. | `shared/reference/facts/upload-and-scan.md` |
| UPL-02 | carried | 2026-10 | 2026-10 | Without a sandbox name it is a policy scan and replaces the compliance verdict. Only one policy scan can be open per profile; a stuck one blocks uploads unless `-deleteincompletescan 1` (which did not clear a build stuck at Pre-Scan Success after a fatal pre-scan; that needed `DeleteBuild`). | `shared/reference/facts/upload-and-scan.md` |
| UPL-03 | carried | 2026-10 | 2026-10 | `-createprofile true` with a misspelled app name silently creates a new empty profile; keep it false and create the profile via the REST API by exact name. The 2026-10 note that the flag must be present even for existing profiles is why the templates always pass it. | `shared/reference/facts/upload-and-scan.md` |
