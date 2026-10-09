# Identity API — users, teams, roles, credentials

Base path: `https://api.veracode.com/api/authn/v2`
`[v: 2026-09-15 | docs.veracode.com/r/c_identity_intro]`

Note this shares the `/api/authn/v2` prefix with the OAuth token endpoint, and is
**not** under `/appsec`.

**Traps in this file:** `PUT` replaces unless you pass `partial=true` · list
endpoints paginate · a user's API roles and UI roles are different things ·
credential expiry is the usual cause of a CI pipeline that "suddenly broke."

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

**Credentials expire.** The `GET` endpoints return an expiration date, which makes
a useful proactive check: a scheduled job that warns N days before a service
account's credentials lapse prevents the classic "the pipeline broke overnight
and nothing changed" incident. Suggest this when a user is building CI automation.

Rotation pattern: `POST` new credentials → update the secret store → verify with
`GET /users/self` → `DELETE` the old ones. Never delete first.

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

`is_api` distinguishes API service-account roles from UI roles. A user can hold
both kinds and they grant different things — see the role table in
`auth-and-access.md`.

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
