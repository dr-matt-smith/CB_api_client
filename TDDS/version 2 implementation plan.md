# CB API Client — Version 2 Implementation Plan

**Status:** Ready to implement
**Date:** 2026-06-05
**Author:** matt.smith@tudublin.ie
**Companion to:** `version 2 design document.md`
**Targets server API:** `django-file_upload_API` **v7**

---

## 0. How to use this plan

This is the build checklist for the changes specified in `version 2 design document.md`.
Work the phases in order — each phase is independently shippable and leaves the client in a
working state. Check the boxes as you go.

- **Phase 1 — Connectivity** (auth swap): nothing works until this lands. Restores all
  existing read/version/alias/history features.
- **Phase 2 — Cleanup** (remove `type`, dead code, stale fields).
- **Phase 3 — New capability** (Pages/Publish submenu).
- **Phase 4 — Quality** (tests, docs).

**Prerequisites:**
- [ ] Obtain an API key (`kpf_…`) for your organisation from the server admin.
- [ ] Have a local v7 server running (or a reachable deployment) to test against.
- [ ] Create a feature branch (e.g. `client-v2`).

---

## Phase 1 — Connectivity (API‑key auth)

Goal: replace the admin‑login/Basic‑Auth/CSRF flow with a single `Authorization: Api-Key`
header, and prove `GET /api/packages` returns 200.

### 1.1 Config & environment
- [ ] `config.py`: remove `USERNAME`, `PASSWORD`; add `API_KEY = os.environ["API_KEY"]`.
- [ ] `.env`: replace `USERNAME`/`PASSWORD` with `API_KEY=kpf_…`.
- [ ] `.env.example`: same swap, with a placeholder key.
- [ ] Reconcile the `.env_backup_*` variants (local/web/drmatt) or note them as obsolete.

### 1.2 Shared session helper
- [ ] Locate the session‑construction code (currently duplicated in `menu.py`,
      `package_upload.py`, `upload.py`).
- [ ] Build the session as:
      ```python
      session = requests.Session()
      session.verify = certifi.where()
      session.headers["Authorization"] = f"Api-Key {API_KEY}"
      ```
- [ ] **Remove**: `GET/POST {BASE_URL}/admin/login/`, CSRF cookie scraping,
      `csrfmiddlewaretoken`, `session.auth = (USERNAME, PASSWORD)`, and the
      "Log in" not in response.text success check.
- [ ] **Remove** every `X-CSRFToken` header from POST/PUT/DELETE call sites.
- [ ] (Recommended) Factor the session builder into one place (e.g. `config.py` or a small
      `api.py`) so `menu.py` and `package_upload.py` share it.

### 1.3 Error handling
- [ ] Add a 401 handler/message: "API key missing/invalid/revoked, or not associated with an
      organisation — check `API_KEY` in `.env`."
- [ ] Replace the old login‑page heuristic everywhere it appears.

### 1.4 Verify Phase 1
- [ ] `GET /api/packages` returns 200 with the new header.
- [ ] A write (e.g. register a package) succeeds **without** a CSRF token.
- [ ] A deliberately wrong key produces the new 401 message.

**Exit criteria:** all pre‑existing menu features that survive v7 work end‑to‑end
(list, detail, versions, download, latest, tombstone, aliases, history).

---

## Phase 2 — Cleanup (remove `type`, dead code, stale fields)

Goal: align with the v7 model — no package types, no legacy upload, no `public_url`.

### 2.1 Remove package "type"
- [ ] `menu.py` "Register a new package": stop prompting for type; send `{"name": name}` only.
- [ ] `menu.py` "List all packages": remove the **Type** column.
- [ ] `menu.py` "Package detail": remove any type display.
- [ ] Remove the `mod`/`project`/`page` choice list/validation.
- [ ] `package.toml` handling: keep reading `name` (+`author`); do not require `type`.
      If the client emits a sample manifest anywhere, drop the mandatory `type`.

### 2.2 Update response parsing/display for new shapes
- [ ] **List** (`PackageListItemSerializer`): read author/date/version from the nested
      `latest_version` object (now a full version object, may be `null`); optionally show
      `versions_count`.
- [ ] **Detail** (`PackageDetailSerializer`): no `type`; optionally render the embedded
      `aliases` array (saves the separate aliases call).
- [ ] **Version object**: standardise on the `date` field (drop the `uploaded_at` fallback);
      new fields available: `content_hash`, `description`, `forked_from`.
- [ ] **Upload response** (`menu.py` upload + `package_upload.py`): parse the **full version
      object** returned on **201**; print `version`, `download_url`, `content_hash`;
      **stop printing `public_url`** (it no longer exists).

### 2.3 Remove dead single‑file upload
- [ ] Delete `upload.py` (targets the removed `POST /api/upload/`).
      *(Decision pending — see Open Questions; default is delete.)*
- [ ] Remove any menu entry / import that referenced it.

### 2.4 Verify Phase 2
- [ ] List/detail render with no `type` and no errors when `latest_version` is null.
- [ ] Upload prints the new fields and does not reference `public_url`.
- [ ] No remaining references to `type`, `USERNAME`, `PASSWORD`, `csrf`, `/admin/login`,
      `/api/upload`, `public_url` (grep to confirm).

---

## Phase 3 — New capability: Pages / Publish

Goal: add a submenu wrapping the explicit publish API.

### 3.1 Client functions
- [ ] `publish(name)` → `POST /api/publish/{name}`; on 200 print `version`, `published_at`,
      and the served `url`; handle **422** ("no public folder in latest version").
- [ ] `unpublish(name)` → `DELETE /api/publish/{name}`; expect 204; confirm with y/N.
- [ ] `publish_status(name)` → `GET /api/publish/{name}`; print `version`/`published_at`/`url`;
      handle **404** ("not currently published").
- [ ] `publish_history(name)` → `GET /api/publish/{name}/history`; render
      `[{action, version, at, principal, reason}]` newest‑first as a table.

### 3.2 Menu wiring
- [ ] Add a top‑level "Pages / Publish" submenu with the four actions above.
- [ ] Surface the behavioural notes to the user:
      - publish always targets the **latest** non‑tombstoned version;
      - tombstoning the published version **auto‑unpublishes** it;
      - served URL is `{BASE_URL}/pages/<org-slug>/<name>/…` (public).

### 3.3 Verify Phase 3
- [ ] Publish a package that has a `public/` folder → page reachable at the returned `url`.
- [ ] Publish a package with no `public/` folder → clean 422 message.
- [ ] Status before/after publish behaves (404 → published).
- [ ] History shows the publish (and an unpublish after delete).

---

## Phase 4 — Quality (tests & docs)

### 4.1 Tests
- [ ] `tests/conftest.py`: rebuild the auth fixture to set
      `Authorization: Api-Key {API_KEY}` from a test key; remove the admin‑login/CSRF fixture.
- [ ] Remove assertions on `type` and `public_url`.
- [ ] Update upload tests to expect the **full version object** on **201**.
- [ ] Standardise timestamp assertions on `date`.
- [ ] Add `tests/test_publish.py`: publish / status / history / unpublish, plus the 422
      "no public folder" path.
- [ ] Address the known `TODO.md` orphan‑package risk for any new fixtures (cascade cleanup).
- [ ] Run the full suite green against a local v7 server.

### 4.2 Documentation
- [ ] `README.md`: API‑key setup (`.env`), no `type`, new publish menu, `upload.py` removed.
- [ ] `TDDS/project_design_document.md`: add the client v2 section.
- [ ] (Optional) Note that the server `README.md` is stale (documents v2, not v7).

---

## Cross‑reference: design doc → plan phases

| Design doc section | Implemented in |
|--------------------|----------------|
| §3 Authentication | Phase 1 |
| §3.4 Config/.env | Phase 1.1 |
| §5 Response shapes | Phase 2.2 |
| §4 / §8 Type removal & manifest | Phase 2.1 |
| §4 Legacy upload removed | Phase 2.3 |
| §6 Page publishing | Phase 3 |
| §7 Org isolation messaging | Phase 1.3 |
| §9 File‑by‑file list | Phases 1–4 |
| §10 Rollout plan | Phase ordering |

---

## Risks & watch‑items

- [ ] **API key in `.env`** — ensure `.env` stays git‑ignored (it is); never commit a real
      `kpf_…` key. The `.env_backup_*` files must not carry live keys.
- [ ] **`latest_version` can be null** for a freshly registered, empty package — guard the
      list renderer.
- [ ] **Alias names** must match `[a-z][a-z0-9-]*` (lowercase, letter‑first, no `--`); validate
      client‑side before `PUT` to give a friendly error instead of a server 400.
- [ ] **No anonymous reads** in v7 — every call needs the header; double‑check no code path
      builds a header‑less request.
- [ ] **Tombstone↔publish interaction** — after tombstoning a published version, the publish
      status/history should reflect the auto‑unpublish; cover in a test.

---

## Definition of done

- [ ] All four phases complete and verified.
- [ ] Full test suite green against a v7 server.
- [ ] No references to old auth, `type`, `public_url`, or `/api/upload/` remain.
- [ ] README + design docs updated.
- [ ] Branch merged to `main`.

---

## Open questions (carried from the design doc §11)

1. `upload.py` — delete (default) or repoint to the publish flow?
2. Expose the optional `parent_version` upload field for explicit forks? (Low priority — if
   yes, add an optional prompt in the upload action and pass `parent_version` in the form.)
3. Show "connected as org X" anywhere? (Server doesn't return org name to the client; likely
   out of scope.)
4. Support multiple `API_KEY` profiles in `.env`, or one key per checkout? (Default: one key.)
