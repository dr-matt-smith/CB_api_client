# CB API Client — Version 2 Design Document

**Status:** Proposed
**Date:** 2026-06-05
**Author:** matt.smith@tudublin.ie
**Targets server API:** `django-file_upload_API` **v7** ("digital sovereignty" / per‑organisation isolation)

---

## 1. Purpose

The server (`django-file_upload_API`) has had a **major, breaking update to v7**. This
document describes the design changes required in this client so that it can talk to
the new server. It is written as a delta against the current client (which targets the
old server contract documented in `project_design_document.md`).

The v7 server is **not backwards compatible**: authentication, the response shapes, the
package model, and the web‑publishing feature all changed. The current client **cannot
authenticate against v7 at all**, so this is a required upgrade, not an optional one.

---

## 2. Summary of server changes that affect us

The headline v7 changes, and whether they impact the client:

| # | Server change (v7) | Client impact |
|---|--------------------|---------------|
| 1 | **New auth: API‑Key header** (`Authorization: Api-Key kpf_…`). Admin‑login/Basic‑Auth/CSRF flow no longer the intended path. | **Critical** — current login flow is obsolete; client cannot connect without changes. |
| 2 | **Per‑organisation isolation.** Every package/author/key is scoped to an Organisation, derived from the API key. | Medium — implicit via the key; affects naming assumptions and messaging. |
| 3 | **Package "type" removed** (no more `mod`/`project`/`page`). | Medium — remove type prompts, columns, and request fields. |
| 4 | **Web publishing is now explicit** via `/api/publish/<name>` (was implicit auto‑extract of `type=page/app`). Pages served at `/pages/<org-slug>/<name>/`. | Medium — new menu area; `public_url` no longer returned by upload. |
| 5 | **Response shapes changed** (list/detail/upload). `type` gone, `latest_version` is now a full object, detail includes `aliases`, upload returns the full version object (no `public_url`). | Medium — display/parsing code must be updated. |
| 6 | **Legacy single‑file endpoints removed** (`/api/upload/`, `/api/files/…`). | Medium — `upload.py` is dead and must be removed or repointed. |
| 7 | **Trailing slashes optional** (`/?$` on every route). | None — current mixed usage keeps working. |
| 8 | **New optional upload field** `parent_version` for explicit forks; `description` accepted alongside `summary`. | Low — optional enhancement. |

> Note: the server's `README.md` still documents the old **v2** contract and is stale.
> The authoritative sources are `TDDs/project_design_version07.md` and
> `TDDs/version07_implementation_plan.md` in the server repo, plus the live code in
> `file_manager/urls.py`, `views.py`, `serializers.py`, `auth.py`.

---

## 3. Authentication — the critical change

### 3.1 Current client behaviour (to be removed)

The client today authenticates by impersonating a browser against the Django admin:

- `GET {BASE_URL}/admin/login/` to obtain a CSRF cookie (`menu.py:21`, `upload.py:13`, `package_upload.py:18`)
- `POST {BASE_URL}/admin/login/` with `username`, `password`, `csrfmiddlewaretoken`, `next=/admin/` (`menu.py:23`)
- `session.auth = (USERNAME, PASSWORD)` HTTP Basic Auth (`menu.py:20`)
- An `X-CSRFToken: <session csrftoken cookie>` header on every write (POST/PUT/DELETE)

### 3.2 New server behaviour (v7)

Authentication is now `ApiKeyAuthentication` (`file_manager/auth.py`):

- Header: **`Authorization: Api-Key kpf_<prefix>_<secret>`**
- The key encodes the organisation. On success the server sets `request.organisation`;
  the global `HasOrganisation` permission then allows the request.
- Session auth still exists as a *fallback* for a logged‑in user that has a `Membership`,
  but for a programmatic client the API key is the correct mechanism.
- **CSRF is not required** when using API‑Key auth (CSRF enforcement is a
  `SessionAuthentication` concern). The entire CSRF dance goes away.
- Auth failures return **401** (the auth class sets `authenticate_header`).

### 3.3 Required client changes

1. **Delete** the admin login helper(s): the `GET/POST /admin/login/` calls, the CSRF
   token scraping, and `session.auth = (USERNAME, PASSWORD)`.
2. **Delete** every `X-CSRFToken` header (`menu.py` POST/PUT/DELETE sites, `package_upload.py`).
3. Set a single default header once on the session:
   ```python
   session.headers["Authorization"] = f"Api-Key {API_KEY}"
   ```
4. Keep `session.verify = certifi.where()` (TLS verification is unchanged and correct).
5. On `401`, print a clear message ("API key missing/invalid/revoked — check `API_KEY`
   in `.env`") instead of the old "still on login page" heuristic.

### 3.4 Config / `.env` changes

Replace credential‑based config with a key:

| Old (`config.py`, `.env`) | New |
|---------------------------|-----|
| `BASE_URL` | `BASE_URL` (unchanged) |
| `USERNAME` | *removed* |
| `PASSWORD` | *removed* |
| — | `API_KEY` (the `kpf_…` key issued by the server admin for your org) |

New `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ["BASE_URL"].rstrip("/")
API_KEY  = os.environ["API_KEY"]
```

New `.env.example`:
```
BASE_URL=https://yourusername.pythonanywhere.com
API_KEY=kpf_xxxxxxxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Operational note: API keys are shown **once** at issuance on the server and stored only
> as a salted hash. The README/onboarding should tell users to obtain a key from their
> org admin and paste it into `.env`. There is no self‑service login.

---

## 4. Endpoint map: client today → server v7

All endpoints are under `{BASE_URL}/api/`. Server routes accept an optional trailing
slash (`/?$`), so existing client URLs continue to match.

| Feature | Client call today | v7 server route | Verdict |
|---------|-------------------|-----------------|---------|
| List packages | `GET /api/packages/` | `GET /api/packages` | OK (response shape changed — §5) |
| Register package | `POST /api/packages/` `{name,type}` | `POST /api/packages` `{name}` | **Drop `type`** |
| Package detail | `GET /api/packages/{name}` | same | OK (shape changed — §5) |
| Delete package | `DELETE /api/packages/{name}` `{reason}` | same | OK |
| List versions | `GET /api/packages/{name}/versions/` | same | OK |
| Version detail | `GET /api/packages/{name}/versions/{n}/` | same | OK |
| Upload version | `POST /api/packages/{name}/versions/` (multipart `file`,`summary`) | same (+optional `description`,`parent_version`) | OK (response shape changed — §5) |
| Download version | `GET /api/packages/{name}/versions/{n}/download/` | same | OK (410 if tombstoned) |
| Download latest | `GET /api/packages/{name}/latest/` | same | OK |
| Tombstone version | `DELETE /api/packages/{name}/versions/{n}/` `{reason}` | same | OK |
| List aliases | `GET /api/packages/{name}/aliases/` | same | OK |
| Set alias | `PUT /api/packages/{name}/aliases/{alias}` `{version}` | same | OK (alias must match `[a-z][a-z0-9-]*`) |
| Remove alias | `DELETE /api/packages/{name}/aliases/{alias}` | same | OK |
| Package history | `GET /api/packages/{name}/history/` | same | OK (markdown text) |
| Version history | `GET /api/packages/{name}/versions/{n}/history/` | same | OK (markdown text) |
| **Publish page** | *(none — was implicit)* | `POST /api/publish/{name}` | **NEW — add** |
| **Unpublish page** | *(none)* | `DELETE /api/publish/{name}` | **NEW — add** |
| **Publish status** | *(none)* | `GET /api/publish/{name}` | **NEW — add** |
| **Publish history** | *(none)* | `GET /api/publish/{name}/history` | **NEW — add** |
| Single‑file upload | `POST /api/upload/` | *removed in v7* | **DELETE `upload.py`** |

---

## 5. Response‑shape changes (parsing / display)

The serializers changed (`file_manager/serializers.py`). The fields the client renders
must be updated.

### 5.1 Package list — `GET /api/packages`

Old (assumed): `[{name, type, latest_version:{version,author,date}}]`

v7 (`PackageListItemSerializer`):
```json
[
  {
    "name": "string",
    "latest_version": { /* full PackageVersionSerializer object, or null */ },
    "versions_count": 7,
    "created_at": "ISO8601"
  }
]
```
Changes: **`type` removed**; `latest_version` is now the **full version object**;
new `versions_count`, `created_at`.

Client action: remove the **Type** column from the list table (`menu.py` "List all
packages"); read author/date/version from the nested `latest_version` object; optionally
show `versions_count`.

### 5.2 Package detail — `GET /api/packages/{name}`

v7 (`PackageDetailSerializer`):
```json
{
  "name": "string",
  "created_at": "ISO8601",
  "versions": [ /* PackageVersionSerializer, newest first */ ],
  "aliases": [ { "name": "...", "version": 3, "updated_at": "ISO8601" } ]
}
```
Changes: **`type` removed**; **`aliases` now embedded** in detail. Client action: drop
type display; can show aliases from detail (saves a round‑trip).

### 5.3 Version object — `PackageVersionSerializer`

```json
{
  "package": "string",
  "version": 3,
  "author": "string",
  "date": "ISO8601",
  "summary": "string",
  "description": "string",
  "content_hash": "string",
  "download_url": "/api/packages/{name}/versions/3/download",  // null if tombstoned
  "tombstoned": false,
  "tombstone_reason": "",
  "forked_from": { "package": "...", "version": 1 }            // or null
}
```
Notes: the canonical timestamp field is **`date`** (the current client already falls back
between `date`/`uploaded_at`; standardise on `date`). `tombstoned` is a boolean (already
handled). New fields available to display: `content_hash`, `description`, `forked_from`.

### 5.4 Upload response — `POST .../versions/`

Old: `{package, version, author, download_url, public_url}`

v7: returns the **full `PackageVersionSerializer`** above (HTTP **201**).
**`public_url` no longer exists** (publishing is now a separate explicit step).

Client action (`menu.py` upload, `package_upload.py`): stop printing `public_url`; print
`download_url`, `version`, `content_hash`. If the user wants a web page, direct them to
the new Publish action (§6).

---

## 6. New feature: explicit page publishing

In the old server, packages of `type = page/app` were auto‑extracted to `/public/<name>/`
on every upload. v7 removes that and replaces it with an **explicit, audited** publish API
that serves the `public/` subfolder of the **latest** version to
`/pages/<org-slug>/<name>/`.

Endpoints:

- `POST /api/publish/{name}` → publishes latest version's `public/` folder.
  Response: `{ "package", "version", "published_at", "url" }`.
  `422` if the latest version has no `public/` folder.
- `DELETE /api/publish/{name}` → unpublish (removes served files). `204`.
- `GET /api/publish/{name}` → current published version + timestamp; `404` if not published.
- `GET /api/publish/{name}/history` → append‑only publish/unpublish log, newest first:
  `[{ action, version, at, principal, reason }]`.

Behavioural notes to surface in the UI:
- Publishing always targets the **latest** non‑tombstoned version — you cannot publish an
  arbitrary old version.
- Tombstoning the currently‑published version **auto‑unpublishes** it (recorded with
  `reason: "tombstoned"`).
- The served URL is `{BASE_URL}/pages/<org-slug>/<name>/...` (public, unauthenticated).

Client action: add a new **"Pages / Publish"** submenu in `menu.py`:
1. Publish latest version of a package
2. Unpublish a package
3. Show current publication status (prints the served `url`)
4. Show publication history

---

## 7. Per‑organisation isolation — implications

The API key determines the organisation; the client never sends an org id explicitly.
Consequences worth handling/communicating:

- Package and author names are now **unique per organisation**, not globally. Two orgs may
  each have a package named `notes`; the client only ever sees its own org's packages.
- All routes require a valid org context, so **there is no anonymous/public read** any more —
  every `/api/…` call must carry the `Authorization` header (the old "reads are public"
  assumption is gone).
- The 401/403 messaging should mention "key not associated with an organisation" as a
  possible cause.

---

## 8. Package manifest (`package.toml`) changes

The uploaded ZIP still must contain a `package.toml`; the server reads the package **name**
and **author** from it. The **`type`** field is now **ignored** (forward‑compatible — it may
be present, but is no longer required or used).

Client action:
- `package_upload.py` / menu upload: keep extracting `name` from `package.toml`; do **not**
  require or prompt for `type`.
- If the client generates a sample/template manifest anywhere, drop the mandatory `type`.
- To web‑publish, the ZIP should contain a `public/` subfolder (consumed by `POST /api/publish`).

---

## 9. File‑by‑file change list

### `config.py`
- Remove `USERNAME`, `PASSWORD`; add `API_KEY`. (§3.4)

### `.env`, `.env.example` (and the `.env_backup_*` variants)
- Replace `USERNAME`/`PASSWORD` with `API_KEY`. (§3.4)

### `menu.py`
- Remove admin‑login + CSRF flow; set `Authorization: Api-Key …` header on the session. (§3.3)
- Remove all `X-CSRFToken` headers from write calls.
- "List all packages": remove **Type** column; read from nested `latest_version`; show `versions_count`. (§5.1)
- "Register package": stop sending/prompting `type`. (§4, §8)
- "Package detail": remove type; optionally render embedded `aliases`. (§5.2)
- "Upload version": stop printing `public_url`; print `download_url`/`content_hash`; parse 201 full version object. (§5.4)
- Add **Pages/Publish** submenu (4 actions). (§6)
- Improve `401` handling/messaging. (§3.3, §7)

### `package_upload.py`
- Same auth swap (drop login/CSRF, add `Authorization` header).
- Stop printing/relying on `public_url`; handle the full version object on 201. (§5.4)

### `upload.py`
- **Remove** (or repoint): targets the deleted `POST /api/upload/`. Single‑file upload is no
  longer a server feature. If a "publish a web page" convenience is wanted, point users at the
  new publish flow instead. (§4, §6)

### `requirements.txt`
- No new runtime deps required (still `requests`, `python-dotenv`, `certifi`). `package.toml`
  parsing already in place.

### `tests/`
- Update `conftest.py` auth fixture: build the session with the `Authorization: Api-Key …`
  header from a test `API_KEY` instead of the admin‑login/CSRF fixture.
- Remove assertions on `type` and on `public_url`.
- Add tests for the new `/api/publish/{name}` endpoints (publish / status / history / unpublish,
  and the 422 "no public folder" path).
- Update expected upload response to the full version object (201).

### `README.md` / `TDDS/project_design_document.md`
- Document v2 of the client: API‑key auth, no type, new publish menu, removal of `upload.py`.

---

## 10. Migration / rollout plan

1. **Obtain an API key** for your organisation from the server admin; put it in `.env` as `API_KEY`.
2. Implement the **auth swap** first (config + session header + remove CSRF). Nothing else works
   until this is done — verify with a simple `GET /api/packages` returning 200.
3. Update **response parsing/display** (list, detail, upload) for the new shapes.
4. Remove **`type`** everywhere; remove **`upload.py`**.
5. Add the **Pages/Publish** submenu.
6. Update **tests** and run the suite against a local v7 server.
7. Update **README** and client design docs.

### Suggested sequencing for low‑risk delivery
- **Phase 1 (connectivity):** steps 1–3 — restores all existing read/version/alias/history features.
- **Phase 2 (cleanup):** step 4 — remove dead code and stale fields.
- **Phase 3 (new capability):** step 5 — publishing.
- **Phase 4 (quality):** steps 6–7.

---

## 11. Open questions / decisions for the maintainer

1. **`upload.py`** — delete entirely, or keep it as a thin wrapper that publishes a page via the
   new `/api/publish` flow? (Recommendation: delete; it no longer maps to anything.)
2. **Fork support** — expose the new optional `parent_version` upload field in the menu, or leave
   it manifest/`history.md`‑driven as before? (Low priority.)
3. **Org display** — the API doesn't return the org name to the client directly; do we want to show
   "connected as org X" anywhere, or is that out of scope? (Could be inferred only via admin.)
4. **Multiple keys / multiple orgs** — should `.env` support more than one `API_KEY` profile, or is
   one key per checkout sufficient? (Recommendation: one key; keep it simple.)

---

## 12. Reference — authoritative server sources

- `file_manager/urls.py` — route table (v7)
- `file_manager/views.py` — view behaviour (upload, publish, tombstone, aliases)
- `file_manager/serializers.py` — response shapes
- `file_manager/auth.py` — `ApiKeyAuthentication` (`Api-Key kpf_<prefix>_<secret>`)
- `file_manager/permissions.py` — `HasOrganisation`
- `TDDs/project_design_version07.md`, `TDDs/version07_implementation_plan.md` — v7 design + checklist
- (The server `README.md` is **stale** — describes v2 — do not rely on it.)
