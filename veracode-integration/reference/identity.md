# Identity API — users, teams, roles, credentials

Base path: `https://api.veracode.com/api/authn/v2`
`[v: 2026-09-15 | docs.veracode.com/r/c_identity_intro]`

Note this shares the `/api/authn/v2` prefix with the OAuth token endpoint, and is
**not** under `/appsec`.

**Traps in this file:** `PUT` replaces unless you pass `partial=true` · list
endpoints paginate · a user's API roles and UI roles are different things · API
roles can only go on API service accounts · generating new HMAC credentials
revokes the old pair 24 hours later · OAuth clients cannot be created by an admin
*for* another user · credential expiry is the usual cause of a CI pipeline that
"suddenly broke".

---

## Users

| Method | Path | Notes |
|---|---|---|
| `POST` | `/users` | Body: `email_address`, `first_name`, `last_name`, `roles`, `teams` |
| `GET` | `/users` | Query: `page`, `size`, `enabled` |
| `GET` | `/users?user_name={name}` | Exact username match |
| `GET` | `/users?email_address={email}` | **URL-encode the `@` as `%40`** |
| `GET` | `/users/search` | Query: `search_term`, `api_id`, `role_id`, `user_type`, `login_status`, `saml_user`, `team_id` |
| `GET` | `/users/self` | Current caller — no admin role needed |
| `GET` | `/users/by_role/{role_id}` | Users holding a role |
| `PUT` | `/users/{user_id}` | Query: `partial=true` to patch instead of replace |
| `DELETE` | `/users/{user_id}` | |

`GET /users/self` is the best smoke test for a new credential: it needs no admin
role, so a failure there is authentication, and a success followed by a `403`
elsewhere is authorization.

## API credentials

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api_credentials` | Generate for the current user |
| `POST` | `/api_credentials/user_id/{user_id}` | Generate for another user |
| `GET` | `/api_credentials` | Current user's credential + expiration |
| `GET` | `/api_credentials/{api_creds_id}` | Specific credential detail |
| `GET` | `/api_credentials/user_id/{user_id}` | A user's credential expiration |
| `DELETE` | `/api_credentials/{api_creds_id}` | Revoke |
| `DELETE` | `/api_credentials/user_id/{user_id}` | Revoke a user's credentials |

`POST /api_credentials/user_id/{user_id}` works live `[v: 2026-10-02 | live]`:
an administrator gets a new **HMAC** key pair for another user (typically an API
service account) without logging in as them. The response carries `api_id`,
`api_secret` and `expiration_ts` — the only time the secret is shown.

**One active pair per user; generating is the rotation.**
`[v: 2026-10-09 | docs.veracode.com/r/HMAC_credentials]` Generating a new pair
schedules the previous one to stop working **24 hours** later. There is no `PUT`
on credentials.

Rotation pattern: `POST` new credentials → put them in the secret store within
the 24-hour window → verify with `GET /users/self` **signed with the new pair** →
`DELETE` the old credential only if you need the cutover sooner. Never delete
first.

**Credentials expire** — one year by default, the organization's maximum. The
`GET` endpoints return `expiration_ts`, which makes a useful proactive check: a
scheduled job that warns N days before a service account's credentials lapse
prevents the classic "the pipeline broke overnight and nothing changed" incident.
Suggest this when a user is building CI automation (`recipes.md` §5).

**Before generating keys for an account, check it holds API roles**
(`GET /users/{user_id}`, `roles[].is_api`). Without them the new keys
authenticate and every call returns `403`. API roles can only be assigned to API
service accounts — a human user returns
`400 "Cannot assign API roles to human user"` `[v: 2026-09-15 | live]`.

## OAuth client credentials
`[v: 2026-10-02 | Identity API spec 1.5 (SwaggerHub Veracode/veracode-identity_api), docs.veracode.com/r/OAuth_Client_credentials]`

A separate credential from the HMAC API credentials above.

| Method | Path | Notes |
|---|---|---|
| `POST` | `/oauth2/client_credentials` | Create for **the caller**. Body: `name`, `description`, `expiration_days` (string), `is_scoped`, `roles[]`, `permissions[]` |
| `GET` | `/oauth2/client_credentials` | Caller's clients. Paged (`page`, `size`; spec calls it `pageable`), `deleted=true` for revoked |
| `GET` | `/oauth2/client_credentials/user/{userId}` | Admin: a user's clients |
| `DELETE` | `/oauth2/client_credentials/user/{userId}` | Admin: revoke all of a user's clients |
| `DELETE` | `/oauth2/client_credentials/user/{userId}/tokens` | Admin: revoke all tokens from a user's clients |
| `GET` / `DELETE` | `/oauth2/client_credentials/{clientId}` | One client / revoke it |
| `DELETE` | `/oauth2/client_credentials/{clientId}/tokens` | Revoke all tokens from one client |
| `GET` / `POST` | `/oauth2/client_credentials/{clientId}/secrets` | Secret metadata / issue a new secret (same `client_id`) |
| `GET` / `DELETE` | `/oauth2/client_credentials/{clientId}/secrets/{secretId}` | One secret's metadata / revoke it |

**`POST` needs at least one role or permission**, even with `is_scoped: false`.
Without one it returns `400 "At least one role or permission is required."`
`[v: 2026-10-02 | live]`. Roles are sent as `[{"role_description": "Results API"}]`.
The safe source is the owner's own API roles from `GET /users/{user_id}`.
`expiration_days` is a string, up to 365.

**No admin "create for another user" endpoint exists** (no `POST` under
`/user/{userId}`). To create or rotate an OAuth client for a service account
without logging in as it:

1. `POST /api_credentials/user_id/{user_id}` → the service account's HMAC keys.
2. `POST /oauth2/client_credentials` **signed with those HMAC keys** → the client
   is owned by the service account.
3. Verify: get a token with the new client and call `GET /users/self`; the
   `user_id` must be the service account's.

In Postman, do this with a request header that the collection pre-request script
reads to choose which key pair signs that one request (signer in
`hmac-and-xml-api.md` §4). To rotate an existing client without changing its
`client_id`, `POST .../{clientId}/secrets`, switch consumers over, then `DELETE`
the old secret by its `secretId`.

Unverified: response field names beyond `client_id` / `client_secret`, the paged
list's `_embedded` key, whether an admin can rotate or revoke another user's
client by `clientId`, and which role a service account needs to create its own
client.

Access tokens: `expires_in` 3599 seen live `[v: 2026-09-15 | live]`; the spec
states 3600.

## Roles and permissions

| Method | Path | Notes |
|---|---|---|
| `GET` | `/roles` | Query: `page`, `size`, `permission_name` |
| `GET` | `/roles/{role_id}` | Role detail with permissions |
| `POST` | `/roles` | Body: `role_name`, `role_description`, `permissions`, `is_api` |
| `PUT` | `/roles/{role_id}` | Query: `partial=true`, `incremental=true` |
| `DELETE` | `/roles/{role_id}` | **Custom roles only** |
| `GET` | `/permissions` | Query: `page` |
| `POST`/`GET`/`PUT`/`DELETE` | `/roles_disabled[/{role_id}]` | Disable/re-enable a role org-wide. Body: `org_id`, `role_id`, `disabled` |

`is_api` distinguishes API service-account roles from UI roles. Human users hold
UI roles; API service accounts hold API roles. The exact API role names and what
each grants are in `auth-and-access.md`.

## Teams

| Method | Path | Notes |
|---|---|---|
| `POST` | `/teams` | Body: `team_name` |
| `GET` | `/teams` | Query: `all_for_org=true` |
| `GET` | `/teams/{team_id}` | Includes members |
| `PUT` | `/teams/{team_id}` | Query: `partial=true`, `incremental=true` |
| `DELETE` | `/teams/{team_id}` | |

Teams gate application visibility. "The API returns fewer applications than I see
in the UI" is usually a team-membership difference between the service account
and the human, not a bug. Check team membership before debugging the Applications
API.

## Business units

`POST`/`GET`/`PUT`/`DELETE` on `/business_units[/{business_unit_id}]`.
Body: `bu_name`. `GET /{id}` includes the unit's teams. `PUT` supports
`partial=true`.

## Account and session

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/principal` | Details of the calling identity |
| `DELETE` | `/session/user_id/{user_id}` | Invalidate that user's JWTs |
| `DELETE` | `/session/idp_user_id/{okta_user_id}` | Invalidate by IdP user id |

Session endpoints are the offboarding path — useful in a deprovisioning script
alongside `DELETE /users/{id}` and credential revocation.

---

## `partial` and `incremental`

`PUT` **replaces** the resource by default. Updating one field without
`partial=true` will silently clear the others — including a user's roles or team
memberships.

- `partial=true` — patch semantics, only the supplied fields change.
- `incremental=true` — **add** to a collection rather than replacing it (roles,
  team members).

Always pass `partial=true` on a targeted update, and say why in a comment. This
is the highest-blast-radius mistake in the Identity API: a role-assignment script
without it can strip permissions across an organization.

## Pagination

List endpoints use the same envelope as `/appsec`: `_embedded.<collection>[]`
plus `page.{number,size,total_elements,total_pages}`. Paginate `/users`,
`/teams` and `/roles` — an unpaginated user list silently truncates at the
default page size, which in a deprovisioning or audit script means missing people.

## Auth

Veracode's Identity examples use HMAC. OAuth works for REST generally; if
Identity calls behave differently from `/appsec` calls under OAuth, flag it rather
than assuming a code bug.

Required role for user/team/credential administration: **Administrator** (UI) or
**Admin API** (service account).
