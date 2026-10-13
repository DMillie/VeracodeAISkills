# Platform setup — access, credentials, structure, first scan

**Order that works:** roles and teams → API service account → credentials into a
secret store → choose policies → application profiles → first scan. Each step
assumes the one before it.

---

## 1. Who can do what during setup

| Task | Needs (UI role) |
|---|---|
| Create users, API service accounts, teams | **Administrator** (Team Admin for their own teams) |
| Install a repository-scanning (workflow) integration | **Administrator** or **Security Lead** |
| Create or edit policies | **Policy Administrator** |
| Create application profiles, upload and scan by hand | **Security Lead**, or another role with profile-creation and scan-submission rights, with team access to the app |
| Agent-based SCA (workspaces, agents) | **Workspace Administrator** or **Workspace Editor**, plus **Security Lead** and **Submitter** |

`[v: 2026-10-09 | docs.veracode.com]` — confirm role names against the customer's
platform if a step is refused; the fix is almost always a missing role, not a bug.

## 2. Teams and visibility

Teams decide which application profiles a user or service account can see.

- Create teams that match how the customer owns software (product or business
  unit), **before** creating application profiles, so each profile can be assigned
  as it is created.
- A service account that must see **every** application — reporting, an
  organization-wide integration — needs **No Team Restrictions** (`noteamrestrictionapi`).
  Without it, an API report silently covers only some apps and looks complete.
- "I can see it in the UI but the integration can't" is nearly always team
  membership.

## 3. The API service account

Automation — CI, repository scanning, scripts, reports — runs on an **API
service account**, not a person. A person's keys stop working when they leave,
and a human user **cannot be given API roles** (`400 "Cannot assign API roles to
human user"`), so their keys authenticate and then fail on most calls with `403`.

### Create one in the Platform `[v: 2026-10-09 | docs.veracode.com/r/t_create_users]`

1. Gear icon → **Admin** → **Users** tab → **Add New User**.
2. Enter a name and an email address someone monitors (activation links and expiry
   notices go there).
3. **User Type: API User** (not UI User).
4. **Team Memberships:** the teams it serves, or **No Team Restrictions** for
   organization-wide work.
5. **User Roles:** tick the API roles for its job (below).
6. **Save**. An activation link is emailed, valid for seven days.

### API roles by job `[v: 2026-10-09 | docs.veracode.com/r/c_API_roles_details]`

| The account will… | Give it |
|---|---|
| Scan from CI or a workflow integration, creating profiles and sandboxes as needed | **Upload and Scan API** + a scan-type role (e.g. static) |
| Scan only into profiles that already exist | **Upload API – Submit Only** + a scan-type role |
| Read results for reports or ticket sync | **Results API** (+ **No Team Restrictions** for the whole portfolio) |
| Run the Reporting (Analytics) API | **Reporting API User** |
| Approve or reject mitigations | **Mitigation API** |
| Manage users, teams and credentials | **Admin API** |

Least privilege still applies: one account per purpose is easier to audit and
rotate than one account with every role.

## 4. Credentials

### Two kinds — know which one a tool wants

| | HMAC API credentials | OAuth client credentials |
|---|---|---|
| What | API ID + secret key (hex) | `client_id` + `client_secret` |
| Used by | **Every CI plugin, the workflow integrations, the Veracode CLI (`veracode configure`), the Pipeline Scan JAR, the Java and Python wrappers** | Your own REST scripts and BI tools (Power BI) |
| Since | Long-standing | GA December 2025 |

When onboarding docs, plugins or integrations say "API ID and key", they mean
**HMAC**.

### Generate HMAC credentials in the Platform `[v: 2026-10-09 | docs.veracode.com/r/REST_APIs_Quickstart]`

Signed in **as the account that will own them**: user account dropdown → **API
Credentials** → **Generate API Credentials** → **HMAC credentials** → **Generate**.
Copy the ID and key straight into the secret store — the key is shown once.

- If **API Credentials** is missing on a first sign-in, refresh, or sign out and
  back in.
- An administrator can also generate a service account's keys without signing in
  as it, through the Identity API (`POST /api/authn/v2/api_credentials/user_id/{id}`).
  That is scripting territory — the veracode-integration skill covers it.

### Lifecycle — put these on a calendar `[v: 2026-10-09 | docs.veracode.com/r/HMAC_credentials]`

- **One active pair per user.** Generating a new pair revokes the old one **24
  hours later** — that is the window to update every place it is stored.
- Credentials **expire after one year** (the organization maximum). An expired
  key is the classic "nothing changed and every pipeline broke overnight". Note
  the expiry date when you create it.

### Regions

A key generated in the European or US Federal region only works against that
region's hosts (`api.veracode.eu` / `api.veracode.us`, and the matching
`analysiscenter.veracode.*`). Most tools pick this up from the key's prefix;
anything with a hardcoded US host fails with a confusing `401`.

## 5. Policies

A policy defines pass/fail: allowed severities, CWE rules, scan frequency, and
grace periods for fixing.

- **Start with a Veracode Recommended policy.** Setting an application's
  **Business Criticality** picks a default (Very Low → *Veracode Recommended Very
  Low*). The workflow integrations default to **`Veracode Recommended Medium +
  SCA`** for profiles they create.
- Customise later, once real results show what is achievable. A custom policy
  written before the first scan is usually wrong in both directions.
- Grace periods are what turn "failing today" into "you have 30 days" — explain
  them before the first verdict lands.
- Only **policy scans** produce the compliance verdict. Sandbox scans are
  evaluated against the same policy for information but never change it, and
  Pipeline Scans never reach the Platform at all.

## 6. Application profiles

One profile per **deployable application** — the thing that gets a compliance
verdict — not necessarily one per repository.

- **Decide the naming convention before any automation runs.** Integrations
  create profiles with their own names: GitHub `{organization}/{repository}`,
  Azure DevOps `ADO/{organization}/{project}/{repository}`, GitLab
  `GITLAB/{group}/{repository}`, the GitHub upload-and-scan action
  `${{ github.repository }}` by default. A hand-made "Payments" profile plus an
  automatic `acme/payments-service` profile splits one app's history in two.
- Set **Business Criticality** (drives the default policy) and assign the owning
  **team** as you create it.
- **Sandboxes** are for development and feature-branch scans without touching
  the verdict. If the customer will want "results of the latest release build",
  keep release scans out of the sandboxes branches use, or name release scans
  unmistakably.

### Create one in the UI `[v: 2026-10-09 | docs.veracode.com/r/Static_Analysis_Quickstart]`

**My Portfolio** → **Applications** → **Add New Application** → name, **Business
Criticality** (the **Policy** follows), **Access** → **Edit** → add the team →
**Save** → **Submit**.

## 7. The first scan, by hand

Doing one application by hand before automating proves the packaging and shows
people what results look like.

1. Package the app — `veracode package` (see `cli-and-packaging.md`) or the
   language's manual packaging rules.
2. Open the application → **Start a Scan** → **Start a Static Scan**. Give it a
   meaningful scan name. For the first run, set **Auto-Scan after Prescan** to
   **Off** so you can inspect the prescan.
3. **Save and Continue** → **Select Files** → upload the artifact → **Next**.
4. Wait for the prescan. **Check the Prescan Status column for packaging errors**
   and the module list for what you expect to see.
5. **Select Modules to Scan** → select the entry points (the
   **Entry Point?** column marks top-level modules) → **Start Scan** (European or
   US Federal accounts: **Review and Submit** → **Submit Scan**).
6. Emails arrive at submission, partial results and completion. Results:
   the application → **Triage Flaws**.

**It worked when** the module list matches the app, the scan completes, and the
flaw count is plausible for an application of that size. Zero or near-zero flaws
on a large first scan is a packaging question until proven otherwise.

---

## Where it goes wrong

| Symptom | Usual cause |
|---|---|
| Keys authenticate, then most calls or scans fail with `403` | The keys belong to a **human** user, or the service account lacks the role for that action |
| Integration or report sees fewer apps than the UI | Team membership; add **No Team Restrictions** where org-wide access is intended |
| `401` from a tool that worked yesterday | Credentials expired (one year), or were regenerated more than 24 hours ago and the old pair is still in use |
| `401` from the first run in an EU or Federal account | A tool pointed at the US host |
| Plugin rejects the "secret" | An OAuth `client_secret` was used where an HMAC key is required |
| First scan finds almost nothing | Packaging — check the prescan and module list before celebrating |
| Two profiles for one app | A manual profile and an integration-created profile with different names |
| Fixed everything in a sandbox, verdict unchanged | Only policy scans change compliance |
