


Version 1 features
==================
- [x] after successful uploading, please  print out a hyperlink to the published folder where the uploaded ZIP folder will have been published
  - e.g. for son-of-fungus.zip the URL is: https://antulcha.eu.pythonanywhere.com/media/public/son-of-fungus
 
- [x] please create a transcript of your work, and my prompts, in the transcripts folder
  - named for the version (so version1_transcript.md for this one, version 2 next and so on)


Version 2 features
==================
Adds a full interactive client (`menu.py`) covering every endpoint exposed by
the Django API, replacing the upload-only script from v1.

- [x] interactive menu loop with session-based login (Django admin + CSRF)
  - credentials read from `.env` via `config.py` (`BASE_URL`, `USERNAME`, `PASSWORD`)

- [x] browse packages
  - list all packages (`GET /api/packages/`)
  - show package detail with all versions inline (`GET /api/packages/<name>/`)
  - show package history (`GET /api/packages/<name>/history/`)
  - list versions for a package (`GET /api/packages/<name>/versions/`)
  - show metadata for a single version (`GET /api/packages/<name>/versions/<n>/`)

- [x] downloads
  - download a specific version (`GET /api/packages/<name>/versions/<n>/download/`)
  - download the latest version (`GET /api/packages/<name>/latest/`)
  - downloaded ZIPs are written to `downloads/<YYYY_MM_DD_HH_MM_SS>/` so each run is kept separate
  - version number is recovered from the `Content-Disposition` header for the latest-download path

- [x] uploads
  - upload a ZIP either by picking from `files_to_upload/` or by entering a full path
  - package name is auto-extracted from `package.toml` inside the ZIP (no need to type it)
  - optional summary message attached to the upload
  - on success prints the returned `download_url` and `public_url` (handy for QR codes / sharing)

- [x] write operations (auth-required)
  - register a new empty package with type `mod`/`project`/`page` (`POST /api/packages/`)
  - tombstone a single version with optional reason (`DELETE /api/packages/<name>/versions/<n>/`)
  - cascade-tombstone an entire package (`DELETE /api/packages/<name>/`)

- [x] aliases sub-menu
  - list aliases for a package (`GET /api/packages/<name>/aliases/`)
  - set / move an alias to a version (`PUT /api/packages/<name>/aliases/<alias>/`)
  - remove an alias (`DELETE /api/packages/<name>/aliases/<alias>/`)

- [x] safety / UX
  - destructive actions (delete package, tombstone version) require y/N confirmation
  - tombstoned download attempts surface the `410 Gone` response cleanly
  - every request prints the HTTP method + URL before firing, so the user can see exactly which endpoint is being called


Version 3 features
==================
Reorganises the client into an API-shaped hierarchy and adds support for the
new version-scoped history endpoint.

- [x] hierarchical menu mirroring the API resource layout
  - top-level sections: Packages / Versions / Aliases / History / Download latest
  - each sub-menu line annotates the HTTP verb + URL pattern it calls, so the user sees exactly which endpoint maps to each option
  - "Download latest" is kept as a direct top-level shortcut rather than a single-item sub-menu

- [x] new endpoint: history as-of a specific version (`GET /api/packages/<name>/versions/<n>/history/`)
  - rendered chronology up to version `n` (versions > n are absent), including the hash for version `n`
  - tombstoned `n` returns 200 with a `(tombstoned)` marker and no hash line
  - unknown `n` returns 404, surfaced cleanly to the user

- [x] menu structure
  - **Packages**: list all / show metadata / register empty / cascade-delete
  - **Versions**: list / detail / publish (upload) / download specific / tombstone
  - **Aliases**: list / set or move / remove
  - **History**: full chronology / as-of-version (new)
  - **Convenience**: download latest version


Client Version 2 (targets server API v7)
=========================================
Major update to talk to the **v7** ("digital sovereignty" / per-organisation
isolation) server. See `version 2 design document.md` and
`version 2 implementation plan.md` in this folder for the full spec.

- [x] **authentication rewritten** — API-key instead of admin login + CSRF
  - `.env` now holds `BASE_URL` + `API_KEY` (`USERNAME`/`PASSWORD` removed)
  - new shared `api.make_session()` sets `Authorization: Api-Key <key>` once and
    installs a 401 hint hook; `menu.py` `connect()` does a connectivity check
  - all `X-CSRFToken` headers removed (not needed with API-key auth)

- [x] **package type removed** (no more `mod`/`project`/`page`)
  - register sends `{name}` only; list drops the **Type** column (adds **Vers** count);
    detail drops type and now renders the embedded `aliases`
  - `package.toml` `type` is ignored by the server (kept forward-compatible)

- [x] **response shapes updated for v7**
  - list item: nested full `latest_version` object + `versions_count` + `created_at`
  - standardised on the `date` field (dropped the `uploaded_at` fallback)
  - upload returns the full version object (no `public_url`); prints `content_hash`

- [x] **new Pages / Publish sub-menu** (explicit web publishing)
  - publish latest (`POST /api/publish/<name>`), unpublish (`DELETE`), status (`GET`),
    history (`GET /api/publish/<name>/history`)
  - serves the latest version's `public/` folder to `/pages/<org-slug>/<name>/`;
    handles `422` (no `public/` folder) and `404` (not published)

- [x] **legacy single-file upload removed**
  - `upload.py` deleted (its `/api/upload/` endpoint no longer exists in v7)

- [x] **tests updated** — fixtures use the API key (no login/CSRF), `type`/`public_url`
  assertions dropped, new `test_publish.py` covering the publish lifecycle, 422, and 404


Client Version 4 (targets server API v8)
=========================================
Update to talk to the **v8** server, whose headline change is that **pages are
fully decoupled from packages**. The package half of the API is unchanged, so
this is a **pages-only** update. See `version 4 design document.md` and
`version 4 implementation plan.md` for the full spec.

> The client jumps **v2 → v4** (no v3 release) so the previous client stays
> clearly labelled v2; the `version 2 …` docs keep their names.

- [x] **pages are now standalone uploads** (no longer a package's `public/` folder)
  - a page is its own ZIP whose root is the served site, plus a `pages.toml`
    manifest with `[publish].path` (e.g. `dev/chess24`)
  - served at `/pages/<org-slug>/<path>/`; re-uploading a path replaces it
  - package upload / tombstone / delete **never** affects a page

- [x] **publish API replaced** — `/api/publish/<name>` → `/api/pages`
  - publish (`POST /api/pages`, multipart page ZIP), list (`GET /api/pages`),
    detail (`GET /api/pages/<path>`), unpublish (`DELETE /api/pages/<path>`)
  - the old `/api/publish/<name>/history` endpoint is gone (no v8 equivalent)

- [x] **new Pages submenu** — publish (upload ZIP) / list / detail / unpublish
  - pages selected by **path** (multi-segment; URLs use `quote(path, safe='/')`)
  - handles `201`, `409` (path overlap), `422` (bad/no `pages.toml`), `404`
  - `_choose_upload_file()` factored out of the package upload flow and reused

- [x] **tests updated** — `make_page_zip` helper, `published_page`/`page_path`
  fixtures, new `test_pages.py` (lifecycle, served page, 422/404/409, and a
  pages-independent-of-packages decoupling test); old `test_publish.py` removed

- [x] **unchanged** — API-key auth (`api.py`, `config.py`) and the package upload
  path (`package_upload.py`) carry over from v2 untouched


Client Version 5 (targets server API v9 + v10 + v11)
=====================================================
Update to talk to the rebranded **Celbridge Workshop API** server, which shipped
three contract-alignment versions in a row. This is a single client release
(**v4 → v5**) covering all three. See `version 5 design document.md` and
`version 5 implementation plan.md` for the full spec.

- [x] **Workshop Key cutover (v11)** — keys now start with `cel_`; the server
  rejects old `kpf_` keys outright (no compatibility window)
  - `config.py` / `api.py` comments and the 401 hint mention the `cel_` marker
  - `api.py` warns at startup if `API_KEY` still begins with `kpf_`
  - the key in `.env` must be re-issued as `cel_…` when the v11 server deploys

- [x] **version read-back renames (v9)** — `tombstoned` → `deleted`,
  `tombstone_reason` → `delete_reason`, `forked_from` → `base`
  - `show_package_detail` / `list_package_versions` relabel the `Tomb` column
    to `Del` and read `deleted`
  - `show_version_detail` reads `deleted` / `delete_reason` and prints
    `Base: name@version` (or `none`); the 410 download wording softened to "deleted"
  - `set_alias` / `delete_alias` refuse the reserved `latest` keyword client-side

- [x] **publish form fields (v10)** — `author` and `path` sent as multipart form
  fields on publish; page manifest reader accepts singular `page.toml` (preferred)
  or plural `pages.toml`
  - optional `AUTHOR` in `.env` is sent so publishes are attributed (not `service`)
  - `package_upload.py` mirrors the `author` form field

- [x] **identity + connection check (v11)** — `connect()` probes
  `GET /api/whoami`, distinguishing a rejected key (401) from an unreachable host,
  and prints which workshop the key binds to

- [x] **tests updated** — `conftest` skip-guard uses `/api/whoami`; `make_page_zip`
  emits singular `page.toml`; `test_versions` asserts `deleted` after delete; new
  `test_whoami.py` (200 + `organisation`)

