# CB API Client — Version 4 Implementation Plan

**Status:** Implemented
**Date:** 2026-06-05
**Author:** matt.smith@tudublin.ie
**Companion to:** `version 4 design document.md`
**Targets server API:** `django-file_upload_API` **v8** (pages decoupled from packages)
**Supersedes:** Client **v2** (`version 2 implementation plan.md`)

---

## 0. How to use this plan

This is the build checklist for the changes specified in
`version 4 design document.md`. The scope is **pages only** — the package /
version / alias / history / download code from v2 is unchanged and needs no work.

- **Phase 1 — Pages rewrite** (menu): replace the `/api/publish/*` flow with the
  standalone `/api/pages` flow.
- **Phase 2 — Tests**: swap the page fixture and the test module.
- **Phase 3 — Docs**: README + design docs.

**Prerequisites:**
- [x] An API key (`kpf_…`) for your organisation in `.env` (unchanged from v2).
- [x] A reachable **v8** server to test against.
- [x] A feature branch (e.g. `client-v4`).

---

## Phase 1 — Pages rewrite (`menu.py`)

Goal: the Pages submenu drives the new standalone page endpoints.

### 1.1 Shared file picker
- [x] Extract the "pick from `files_to_upload/` or type a path" block out of
      `upload_package()` into `_choose_upload_file()` (returns a path or `None`).
- [x] Re-point `upload_package()` at the new helper (behaviour unchanged).

### 1.2 Page manifest reader
- [x] Add `_read_pages_toml(zip_path)` — find the top-level `pages.toml`
      (case-insensitive), read `[publish].path`, return `(path, error)`.
- [x] Clear errors for: not a ZIP, no `pages.toml`, missing `path`.

### 1.3 Page API calls
- [x] `get_pages()` → `GET /api/pages`; `list_pages()` renders a table
      (path / published_by / published_at / url).
- [x] `pick_page()` → lists live pages, returns the chosen **path**.
- [x] `publish_page()` → choose a ZIP, read its `pages.toml` path, then
      `POST /api/pages` with multipart `file`; handle **201 / 409 / 422**.
- [x] `show_page_detail()` → `GET /api/pages/{path}`; handle **404**.
- [x] `unpublish_page()` → confirm, then `DELETE /api/pages/{path}`; expect 204.
- [x] Build all page URLs with `quote(path, safe='/')` (preserve segments).

### 1.4 Remove dead publish code
- [x] Delete `publish_status()` and `publish_history()`.
- [x] Replace the old package-based `publish_page()` / `unpublish_page()` bodies.
- [x] Remove all `/api/publish/...` references from `menu.py`.

### 1.5 Menu wiring
- [x] Rewrite `pages_menu()`: 1 Publish / 2 List / 3 Detail / 4 Unpublish.
- [x] Update the top-level item-5 label to
      `Pages (publish / list / detail / unpublish)`.

### 1.6 Verify Phase 1
- [ ] Publish a ZIP containing `pages.toml` → page reachable at the returned `url`.
- [ ] A ZIP with no `pages.toml` → clean 422 message.
- [ ] A path that overlaps an existing page → clean 409 message.
- [ ] List shows live pages; detail of an unknown path → 404.
- [ ] Unpublish removes the page; detail afterwards → 404.

**Exit criteria:** the Pages submenu fully drives `/api/pages`; no `/api/publish`
reference remains; all package/version/alias/history features still work.

---

## Phase 2 — Tests

### 2.1 Helpers
- [x] `helpers.py`: remove the `with_public` branch from `make_zip`.
- [x] Add `make_page_zip(path, marker)` — builds a `pages.toml` + `index.html`
      bundle (the ZIP root is the served site).

### 2.2 Fixtures
- [x] `conftest.py`: remove `published_page_package`.
- [x] Add `page_path` (unique `pytest-pages/<uuid>` path) and `published_page`
      (publishes via `POST /api/pages`, unpublishes on teardown).

### 2.3 Test module
- [x] Replace `tests/test_publish.py` with `tests/test_pages.py`:
  - [x] `test_published_page_is_served` — served URL is public and has the content.
  - [x] `test_page_lifecycle` — publish → list → detail → unpublish → 404.
  - [x] `test_publish_missing_pages_toml_422`.
  - [x] `test_page_detail_unpublished_404`.
  - [x] `test_publish_path_overlap_409`.
  - [x] `test_pages_independent_of_packages` — deleting a package leaves a page intact.

### 2.4 Verify Phase 2
- [ ] `pytest -q` green against a local v8 server.

---

## Phase 3 — Documentation

- [x] `README.md`: v4/v8 banner; new Pages menu + `pages.toml` publish example.
- [x] `TDDS/version 4 design document.md` (this plan's companion).
- [x] `TDDS/project_design_document.md`: add a "Client Version 4" section.
- [x] Keep the `version 2 …` docs as the previous version (no rename needed —
      they are already named `version 2`).

---

## Cross-reference: design doc → plan phases

| Design doc section | Implemented in |
|--------------------|----------------|
| §3 Standalone pages / `pages.toml` | Phase 1.2 |
| §4 Endpoint map | Phase 1.3 / 1.4 |
| §5 Response shapes / status codes | Phase 1.3 |
| §6 Client design | Phase 1 |
| §7 File-by-file list | Phases 1–3 |

---

## Risks & watch-items

- [ ] **Path slashes** — page paths are multi-segment; never `quote(path,
      safe='')` (that would escape `/` and break the route). Use `safe='/'`.
- [ ] **Destructive republish** — uploading an existing path **replaces** it
      silently; the menu prints the target path before sending so the user can
      cancel.
- [ ] **Overlap rules** — a path that is a prefix of, or contained by, a live
      page is rejected (409); siblings coexist. Surfaced as a clean message.
- [ ] **No history endpoint** — do not re-add a "Show page history" action until
      the server provides one.

---

## Definition of done

- [x] Pages submenu drives `/api/pages` (publish / list / detail / unpublish).
- [x] No `/api/publish`, `with_public`, or page-history references remain.
- [ ] `pytest -q` green against a v8 server.
- [x] README + design docs updated; v2 docs retained as the previous version.
- [ ] Branch merged to `main`.
