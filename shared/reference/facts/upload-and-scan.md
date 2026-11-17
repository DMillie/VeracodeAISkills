# Upload and Scan (policy and sandbox) via the API wrapper

- `-action UploadAndScan -vid -vkey -appname -createprofile {true,false} -filepath -version
  -autoscan true -deleteincompletescan 1 [-scantimeout minutes] [-sandboxname -createsandbox true]`.
  **[live 2026-11-11, -help]**
- Without a sandbox name it is a policy scan and replaces the compliance verdict. Only one
  policy scan can be open per profile; a stuck one blocks uploads unless `-deleteincompletescan 1`
  (which did not clear a build stuck at Pre-Scan Success after a fatal pre-scan; that needed
  `DeleteBuild`). **[2026-10]**
- `-createprofile true` with a misspelled app name silently creates a new empty profile; keep it
  false and create the profile via the REST API by exact name. The 2026-10 note that the flag
  must be present even for existing profiles is why the templates always pass it. **[2026-10]**
- Without `-scantimeout` the job returns after the upload: "accepted upload" is not "completed
  scan". With it the wrapper polls and fails the job if the scan does not pass policy.
- Per-branch sandbox names hit the per-application sandbox limit fast; one per long-lived branch.

Tags: **[live <date>]** observed in the lab on that date; **[2026-10, not re-verified]** carried over, check before relying on it.
