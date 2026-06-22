# CB API Client — Version 5 Implementation Plan

**Status:** Implemented
**Date:** 2026-06-22
**Author:** matt.smith@tudublin.ie
**Companion to:** `version 5 design document.md`
**Targets server API:** Celbridge Workshop API **v9 + v10 + v11**
**Supersedes:** Client **v4** (`version 4 implementation plan.md`, targets server v8)

---

## 0. How to use this plan

This is the build checklist for the changes specified in
`version 5 design document.md`. It is a delta against the v4 client; the menu
structure and endpoint paths are unchanged. Work is grouped into four phases:

- **Phase 1 — Auth cutover** (`config.py`, `api.py`): the blocking `cel_` change.
- **Phase 2 — Read/write contract** (`menu.py`, `package_upload.py`): renamed
  fields, new form fields, `whoami` connection check, reserved `latest`.
- **Phase 3 — Tests**: `whoami` skip-guard, `deleted` assertion, `page.toml`.
- **Phase 4 — Docs**: `.env.example`, READMEs, design docs.

**Prerequisites:**
- [x] A **Workshop Key** (`cel_…`) for your organisation in `.env`.
- [x] A reachable **v11** Workshop server to test against.
- [x] A feature branch (e.g. `client-v5`).

---

## Phase 1 — Auth cutover

### 1.1 `config.py`
- [x] Add optional `AUTHOR = os.environ.get("AUTHOR")` (the Workshop Author).
- [x] Update the `API_KEY` comment to `cel_<prefix>_<secret>` / "Workshop Key"
      and note `kpf_` keys are rejected.

### 1.2 `api.py`
- [x] Refresh the module docstring ("Celbridge Workshop API", `cel_` marker).
- [x] Extend `_warn_on_auth_failure` 401 hint with the `cel_`/`kpf_` change.
- [x] Add a startup advisory in `make_session` if `API_KEY` begins with `kpf_`.

**Exit criteria:** a `cel_…` key authenticates; a `kpf_…` key is warned about
before the first call and produces a clear 401 hint.

---

## Phase 2 — Read/write contract (`menu.py`, `package_upload.py`)

### 2.1 Connection check (v11)
- [x] `connect()` probes `GET /api/whoami`; prints the workshop org name (and
      author when present); keeps 401 → exit and error handling.

### 2.2 Renamed read fields (v9)
- [x] `show_package_detail` / `list_package_versions`: read `deleted` (was
      `tombstoned`); relabel the `Tomb` column to `Del`.
- [x] `show_version_detail`: read `deleted` / `delete_reason`; read `base`
      (`name@version` or `none`) in place of `forked_from`.
- [x] `download_package_version`: soften the 410 wording to "deleted".

### 2.3 Reserved `latest` (v9)
- [x] `set_alias` / `delete_alias`: refuse the reserved `latest` keyword
      client-side with a clear message (no server round-trip).

### 2.4 Publish form fields (v10)
- [x] `upload_package`: send `author` form field when `AUTHOR` is set.
- [x] `_read_pages_toml`: accept `page.toml` (preferred) or `pages.toml`.
- [x] `publish_page`: send `path` (and `author` when set) as form fields,
      keeping the bundled manifest.
- [x] `package_upload.py`: mirror the `author` form field.

### 2.5 Verify Phase 2
- [ ] `connect()` prints the workshop name; a bad key still exits cleanly.
- [ ] A deleted version shows `Del = yes` and `Deleted: yes`.
- [ ] A forked version shows its `Base:`; a root version shows `Base: none`.
- [ ] Setting/removing alias `latest` is refused locally.
- [ ] A page bundle with `page.toml` publishes; `author` is recorded when set.

**Exit criteria:** all renamed fields render; `whoami` drives the connection
check; publishes carry `author`/`path`; `latest` is treated as reserved.

---

## Phase 3 — Tests

### 3.1 Fixtures / helpers
- [x] `conftest.py`: skip-guard uses `GET /api/whoami` (401 → skip).
- [x] `helpers.make_page_zip`: emit the singular `page.toml`.

### 3.2 Test modules
- [x] `test_versions.py`: after delete, assert version detail `deleted is True`
      and the download returns 410; reworded from "tombstone".
- [x] New `test_whoami.py`: `GET /api/whoami` → 200 with an `organisation`.

### 3.3 Verify Phase 3
- [ ] `pytest -q` green against a v11 Workshop server.

---

## Phase 4 — Documentation

- [x] `.env.example`: `cel_…` key, optional `AUTHOR`.
- [x] `README.md`: v5/Workshop banner, Workshop Key, `cel_` note, `AUTHOR`,
      `whoami` connection line, `Del` column, `page.toml` note.
- [x] `README_mac_zip.md`: no auth/branding references — no change needed.
- [x] `TDDS/version 5 design document.md` (this plan's companion).
- [x] `TDDS/project_design_document.md`: add a "Client Version 5" section.

---

## Cross-reference: design doc → plan phases

| Design doc section | Implemented in |
|--------------------|----------------|
| §3 `cel_` key marker | Phase 1 |
| §4 v9 read-back contract | Phase 2.2 / 2.3 |
| §5 v10 publish & pages | Phase 2.4 |
| §6 v11 identity / whoami / rebrand | Phases 1–2 / 4 |
| §8 File-by-file list | Phases 1–4 |

---

## Risks & watch-items

- [ ] **Hard `kpf_` cutover** — the `.env` key must be re-issued as `cel_…` at
      the same time the v11 server deploys; the client can only warn early.
- [ ] **`author` null for service keys** — `whoami.author` is `null` for an org
      service key; only display it when present.
- [ ] **Page manifest both names** — the reader accepts `page.toml` and
      `pages.toml`; the bundle still ships a manifest (conservative path).

---

## Definition of done

- [x] `cel_` marker handled (comments, 401 hint, startup warning).
- [x] `deleted` / `delete_reason` / `base` rendered; `latest` reserved.
- [x] `whoami` connection check; `author`/`path` form fields on publish.
- [ ] `pytest -q` green against a v11 server.
- [x] Docs updated; v4 docs retained as the previous version.
- [ ] Branch merged to `main`.
