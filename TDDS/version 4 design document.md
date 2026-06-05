# CB API Client — Version 4 Design Document

**Status:** Proposed
**Date:** 2026-06-05
**Author:** matt.smith@tudublin.ie
**Targets server API:** `django-file_upload_API` **v8** (pages decoupled from packages)
**Supersedes:** Client **v2** (`version 2 design document.md`, targets server v7)

---

## 1. Purpose

The server (`django-file_upload_API`) has had another breaking update, to **v8**.
The headline change: **pages are now completely decoupled from packages**. This
document describes the client changes required to talk to v8. It is written as a
delta against the current client (**v2**, documented in
`version 2 design document.md`), which targets the v7 contract.

The **package** half of the API (packages / versions / aliases / history /
download) is **unchanged** between v7 and v8 — the v2 client already handles it
correctly. The only area that changes for the client is **pages / publishing**.

> Versioning note: the client jumps **v2 → v4** (no v3 release) to leave the
> previous client clearly labelled as v2. The previous design/implementation
> docs keep their `version 2 …` filenames.

---

## 2. Summary of server changes that affect us

| # | Server change (v8) | Client impact |
|---|--------------------|---------------|
| 1 | **Pages decoupled from packages.** A page is no longer a package's `public/` folder; it is its **own ZIP upload** identified by a publish path. | **Critical (pages only)** — the entire publish flow is replaced. |
| 2 | **New pages endpoints** under `/api/pages` (POST/GET/GET `<path>`/DELETE `<path>`). | Replace the `/api/publish/<name>` calls. |
| 3 | **Old publish endpoints removed** (`/api/publish/*`, including `/history`). | Delete the four `publish_*` client functions. |
| 4 | **New manifest `pages.toml`** with `[publish].path` carried inside the page ZIP. | New manifest reader; ZIP no longer needs `public/`. |
| 5 | **Pages keyed on a publish path**, not a package name (multi-segment, e.g. `dev/chess24`). | URL building must preserve `/`; selection is by path, not package. |
| 6 | **No coupling** — uploading/tombstoning/deleting a package never affects a page. | Remove "tombstoning auto-unpublishes" messaging. |
| 7 | Package / version / alias / history API **unchanged**. | None — v2 code stays as-is. |

> Authoritative server sources: `file_manager/urls.py`, `views.py`,
> `serializers.py`, `pages.py`, `pages_parsing.py`, plus the server's
> `TDDs/project_design_version08.md` and `TDDs/version08_implementation_plan.md`.

---

## 3. The core change: pages are standalone

### 3.1 v7 model (what the v2 client does today)

- A page **was** a view of a package: `POST /api/publish/<name>` extracted the
  **latest** version's `public/` subfolder and served it at `/pages/<org>/<name>/`.
- Tombstoning the published version auto-unpublished the page.
- Audit trail via `GET /api/publish/<name>/history`.

### 3.2 v8 model (what the v4 client must do)

- A page is its **own ZIP upload**. The ZIP root **is** the site; everything
  except `pages.toml` is served verbatim.
- The page's location comes from `pages.toml` → `[publish].path` (e.g.
  `dev/chess24`), served at `/pages/<org-slug>/<path>/`.
- Pages have **no relationship** to any package or version. Package operations
  never touch pages.
- Re-uploading the same path **replaces** it (destructive, allowed).

### 3.3 `pages.toml` manifest

Top-level of the page ZIP (case-insensitive match):

```toml
[publish]
path = "dev/chess24"
```

Rules (enforced server-side; the client reads `path` for display / early errors):

- `[publish]` table and `path` key are **required** (missing → 422).
- Path is relative: no leading/trailing slash, no `.`/`..`, no empty segments.
- Each segment matches `^[a-z0-9._-]+$`; ≤ 255 chars total; ≤ 8 segments deep.
- Unknown keys/tables are ignored (forward-compatible).

---

## 4. Endpoint map: v2 client → v8 server

| Feature | v2 client call (remove) | v8 server route (add) | Notes |
|---------|-------------------------|-----------------------|-------|
| Publish page | `POST /api/publish/{name}` (no body) | `POST /api/pages` (multipart `file` = page ZIP) | Path comes from `pages.toml`, not the URL. |
| Unpublish page | `DELETE /api/publish/{name}` | `DELETE /api/pages/{path}` | `204`. |
| Page status/detail | `GET /api/publish/{name}` | `GET /api/pages/{path}` | `404` if not published. |
| List pages | *(none)* | `GET /api/pages` | **NEW** — list all live pages in the org. |
| Publish history | `GET /api/publish/{name}/history` | *(removed)* | No public history endpoint in v8. |

All package/version/alias/history/download routes are **unchanged** — no client
changes there.

---

## 5. Response shapes (v8 pages)

### 5.1 Publish — `POST /api/pages` → **201**

```json
{
  "path": "dev/chess24",
  "url": "/pages/acme/dev/chess24/",
  "published_at": "ISO8601",
  "content_hash": "sha256-hex"
}
```

### 5.2 List — `GET /api/pages` → **200**

```json
[
  {
    "path": "dev/chess24",
    "url": "/pages/acme/dev/chess24/",
    "published_at": "ISO8601",
    "published_by": "alice | service",
    "content_hash": "sha256-hex"
  }
]
```

### 5.3 Detail — `GET /api/pages/{path}` → **200** (same object as a list item)

### 5.4 Status codes the client handles

| Code | Meaning | Client behaviour |
|------|---------|------------------|
| 201 | Published | Print `path`, served `url`, `content_hash`. |
| 200 | List / detail OK | Render. |
| 204 | Unpublished | Confirm removal. |
| 404 | Path not published | "not currently published". |
| 409 | Path overlap (prefix/contained) | "path conflict — overlaps an existing page". |
| 422 | Invalid bundle (no/bad `pages.toml`, bad path) | "invalid page bundle". |

---

## 6. Client design

### 6.1 New / changed `menu.py` functions

- `_choose_upload_file()` — factored out of `upload_package()` so the page
  publish flow reuses the same "pick from `files_to_upload/` or type a path" UX.
- `_read_pages_toml(zip_path)` — reads `[publish].path` from `pages.toml` in the
  ZIP; returns `(path, error)`. Mirrors `_read_package_toml`.
- `get_pages(session)` / `list_pages(session)` — `GET /api/pages` + table render.
- `pick_page(session)` — list pages, select one, return its **path**.
- `publish_page(session)` — choose a ZIP, read its `pages.toml` path, `POST
  /api/pages`; handle 201 / 409 / 422.
- `show_page_detail(session)` — pick a page, `GET /api/pages/{path}`.
- `unpublish_page(session)` — pick a page, confirm, `DELETE /api/pages/{path}`.

### 6.2 Removed `menu.py` functions

- `publish_status` and `publish_history` (the latter has no v8 equivalent).
- The old package-based `publish_page` / `unpublish_page` bodies are replaced.

### 6.3 URL building

Page paths are multi-segment. Build URLs with `quote(path, safe='/')` so the
slashes survive (server route is `(?P<path>.+)`).

### 6.4 Menu wiring

```
--- Pages ---
  1 - Publish a page (upload ZIP)    (POST   /api/pages)
  2 - List published pages          (GET    /api/pages)
  3 - Show page detail              (GET    /api/pages/{path})
  4 - Unpublish a page              (DELETE /api/pages/{path})
  0 - Back
```

The top-level item 5 label becomes `Pages (publish / list / detail / unpublish)`.

---

## 7. File-by-file change list

### `menu.py`
- Extract `_choose_upload_file()`; use it in `upload_package()`.
- Add `_read_pages_toml()`, `get_pages()`, `list_pages()`, `pick_page()`.
- Rewrite `publish_page()` to upload a ZIP to `POST /api/pages`.
- Rewrite `unpublish_page()` and add `show_page_detail()` keyed on path.
- Remove `publish_status()` and `publish_history()`.
- Rewrite `pages_menu()` and the top-level item-5 label.

### `tests/`
- `helpers.py`: drop `make_zip(..., with_public=...)`; add `make_page_zip(path)`.
- `conftest.py`: replace `published_page_package` with `page_path` +
  `published_page` (publishes via `/api/pages`, unpublishes on teardown).
- Replace `test_publish.py` with `test_pages.py`: lifecycle, served page,
  missing-manifest 422, detail-404, overlap-409, and a
  pages-independent-of-packages decoupling test.

### `README.md`
- v4/v8 banner; new Pages menu and `pages.toml` publishing example.

### `config.py`, `api.py`, `package_upload.py`
- **No change** — API-key auth and the package upload path are unchanged in v8.

### `TDDS/`
- Add this document and `version 4 implementation plan.md`.
- Add a "Client Version 4" section to `project_design_document.md`.
- Keep the `version 2 …` docs as the previous version (no rename).

---

## 8. Open questions / decisions

1. **Path entry on unpublish/detail** — select from the live list (chosen) vs.
   free-text path entry? List-and-pick is friendlier and avoids typos; free-text
   is kept implicitly because `pick_page` only lists live pages.
2. **History** — v8 exposes no page-history API. If the server later adds one,
   reintroduce a "Show page history" action. Out of scope for v4.
3. **`published_by`** — shown in list/detail; the client cannot set it (server
   derives it from the API key / principal).
