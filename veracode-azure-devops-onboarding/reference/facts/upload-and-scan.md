# Upload and Scan (policy and sandbox) via the API wrapper

- `-action UploadAndScan -vid -vkey -appname -createprofile {true,false} -filepath -version
  -autoscan true -deleteincompletescan 1 [-scantimeout minutes] [-sandboxname -createsandbox true]`.
  [UPL-01]
- Without a sandbox name it is a policy scan and replaces the compliance verdict. Only one
  policy scan can be open per profile; a stuck one blocks uploads unless `-deleteincompletescan 1`.
  A build stuck at Pre-Scan Success after a fatal pre-scan needs `DeleteBuild`. [UPL-02?]
- `-createprofile true` with a misspelled app name silently creates a new empty profile: keep it
  `false` and create the profile through the REST API by exact name. Always pass the flag, also
  for existing profiles. [UPL-03?]
- Without `-scantimeout` the job returns after the upload: "accepted upload" is not "completed
  scan". With it the wrapper polls and fails the job if the scan does not pass policy.
- Per-branch sandbox names hit the per-application sandbox limit fast: one per long-lived branch.

`[ID]` = entry in the evidence register (`evidence/` in the source repository). `~` = read, not run. `?` = carried over, not re-verified: check before relying on it.
