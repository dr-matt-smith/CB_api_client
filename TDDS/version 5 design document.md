# CB API Client — Version 5 Design Document

**Status:** Implemented
**Date:** 2026-06-21
**Author:** matt.smith@tudublin.ie
**Targets server API:** `django-file_upload_API` **v9 + v10 + v11** (the three contract-alignment versions, now branded *Celbridge Workshop API*)
**Supersedes:** Client **v4** (`version 4 design document.md`, targets server v8)

---

## 1. Purpose

The server has shipped three breaking-ish updates in a row — **v9, v10, v11** —
that together close out the `workshop_server_alignment.md` backlog. This
document describes the changes the **Python CLI client** (`menu.py`,
`package_upload.py`, `api.py`, `config.py`, `tests/`) needs to keep working
against the updated server. It is a delta against the current client (**v4**,
which targets server v8).

> **The server's design docs are written for a different client.** The server's
> `project_design_version09/10/11.md` describe the payoff for the **C# in-app
> Workshop client** (`WorkshopApiSender`, `CredentialConstants`, etc.). This
> document is the parallel work for **our Python client** — the contract changes
> are the same, but the code that consumes them is ours.

> **Every claim here is checked against the server source**, not just the design
> docs, because three "server's-call" decisions (page manifest name,
> content-hash prefix, health-endpoint shape) were only settled in the
> implementation. Authoritative files: `file_manager/auth.py`, `views.py`,
> `serializers.py`, `pages.py`, `pages_parsing.py`, `package_pipeline.py`,
> `urls.py`.

> Versioning note: the client jumps **v4 → v5** (one release covering all three
> server versions). The previous design/implementation docs keep their
> `version 4 …` filenames.

---

## 2. Summary of server changes that affect us

| # | Server change | Version | Client impact |
|---|---------------|---------|---------------|
| 1 | **API-key marker `kpf_` → `cel_`. Old `kpf_` keys are now *rejected* (hard cutover — no compatibility window).** | v11 | **CRITICAL / blocking.** A `kpf_…` key in `.env` gets `401` everywhere. Operator must re-issue a `cel_…` key. |
| 2 | **`tombstoned` → `deleted`** on a version; `tombstone_reason` → `delete_reason`; `description` cleared on delete. | v9 | **Breaking read.** Three render paths read `v["tombstoned"]`; they 'go quiet' (always show *not deleted*). |
| 3 | **`forked_from` → `base`** (`{name, version}` or `null`). | v9 | **Breaking read.** `show_version_detail` reads `forked_from`; provenance stops displaying. |
| 4 | **`content_hash` is now bare lowercase hex** (no `sha256:` prefix), consistent for packages and pages. | v9 | Cosmetic — we only display it. No strip needed. |
| 5 | **`latest_version` excludes deleted versions** (`null` if none live); aliases are static (no auto-repoint/detach on delete); `latest` is a reserved keyword. | v9 | Defensive: handle `null` latest; refuse to create/delete a `latest` alias. `/latest` endpoint **remains**. |
| 6 | **`author` read from a multipart form field** on package *and* page publish (manifest `author` no longer required). | v10 | We should **send `author`** so page `published_by` stops showing `service`. |
| 7 | **`path` read from a multipart form field** on page publish; manifest now **optional**; singular **`page.toml`** accepted (plural `pages.toml` still works). | v10 | Send `path` as a form field; relax/rename the manifest reader. |
| 8 | **Page `url` is now absolute** (`https://host/pages/…`, from server's `CANONICAL_ORIGIN`). | v10 | Already compatible (our `startswith("http")` guard passes it through). Can simplify. |
| 9 | **Stopped injecting `version = N`** into the served `package.toml`. | v10 | None — we never read it. |
| 10 | **`base` accepted on publish** as flat form fields **`base_name` + `base_version`** (returned nested). | v9/v10 | Optional new capability (provenance on upload). |
| 11 | **New `GET /api/whoami`** — `200` + `{organisation, organisation_name, author}` when the key is valid, `401` when not. | v11 | Use it for the connection check + show *which* workshop the key binds to. |
| 12 | **Rebrand** "Celbridge Hub" → "Celbridge Workshop"; the credential is the **Workshop Key**. Endpoint paths unchanged. | v11 | User-facing strings / docs / comments only. |

Items **1–3** break the current client; **5** is a latent bug-guard; everything
else is improvement or no-op.

---

## 3. The blocking change: the `cel_` key marker (v11)

This is the one change that takes the client from "renders slightly wrong" to
"cannot authenticate at all".

- Server `auth.py` now generates `cel_<prefix>_<secret>` and
  `_lookup_and_verify` **rejects** any key whose leading segment is not `cel`
  (`if parts[0] != 'cel': return None`). There is **no** `kpf_` fallback in the
  deployed code.
- Our client sends whatever `API_KEY` is in `.env` verbatim
  (`api.py` → `Authorization: Api-Key {API_KEY}`). It does not inspect the
  marker, so the client itself needs **no parsing change** — but the **key in
  `.env` must be re-issued** as `cel_…` or every request 401s.

**Client work:**
- `config.py`: update the comment (`kpf_…` → `cel_…` "Workshop Key").
- `api.py` `_warn_on_auth_failure`: extend the 401 hint to mention the marker
  change ("v11 keys start with `cel_`; old `kpf_` keys are rejected — re-issue").
- *(Optional, friendly)* add a one-line advisory at startup if `API_KEY` starts
  with `kpf_`: warn before the first call rather than after a 401.
- `.env.example`, `README.md`: show `cel_…` and the *Workshop Key* name.

---

## 4. v9 — package-version read-back contract

### 4.1 The `deleted` rename (was `tombstoned`)

Server `PackageVersionSerializer` now emits `deleted` (bool) and `delete_reason`;
`tombstoned`/`tombstone_reason` are gone, and the publisher `description` is
cleared on delete (version number + `content_hash` retained).

Client reads `v.get("tombstoned")` in **three** places —
`show_package_detail`, `list_package_versions`, `show_version_detail` — plus the
"Tombstoned: yes/no" line in detail. All must read `deleted` /
`delete_reason`. Recommended: relabel the `Tomb` column to `Del` and the detail
line to `Deleted:`.

> The version-download path already handles `410 Gone`; only the wording
> ("tombstoned") needs softening to "deleted".

### 4.2 The `base` back-pointer (was `forked_from`)

`show_version_detail` reads `forked_from` → must read `base`:

```python
base = v.get("base")            # {"name": "...", "version": N} or null
if base:
    print(f"Base: {base.get('name')}@{base.get('version')}")
else:
    print("Base: none")
```

**Optional new capability:** the publish endpoints accept provenance as **flat
form fields `base_name` + `base_version`** (the server returns them nested as
`base`). A CLI has no install-record to read a base from, so this stays optional
— if added, prompt for "base package@version" on upload and split it into the
two fields.

### 4.3 `content_hash` format

Now bare lowercase hex for both packages and pages (server uses
`hashlib.sha256(...).hexdigest()` with no prefix). We only print it, so no code
change is required; any defensive prefix-stripping can be dropped.

### 4.4 Aliases static + `latest` client-resolved

- `list_packages` / `pick_package` read `latest_version`, which the server now
  computes excluding deleted versions and returns `null` when none are live. Our
  existing `p.get("latest_version") or {}` already tolerates `null` — confirm,
  keep.
- The server no longer auto-repoints/detaches aliases on delete. No client code
  reacts to that today, so nothing breaks; we should **stop treating `latest` as
  mutable**: `set_alias` / `delete_alias` should refuse `latest` (reserved
  keyword) with a clear message instead of round-tripping to the server.
- `GET /api/packages/{name}/latest` **remains** in `urls.py`, so
  `download_package_latest` keeps working as-is. (Long-term we could compute
  latest from metadata, but it is not required for v5.)

---

## 5. v10 — publish & pages ingestion contract

### 5.1 Send `author` on publish (packages and pages)

The server reads `author` from the multipart form
(`request.data.get('author')`) and persists it as the version author / page
`published_by`. Today our client sends **no** `author`, so service-key page
publishes show `published_by: "service"`.

**Design decision — where does `author` come from?** Add an optional
`AUTHOR` to `.env`/`config.py` (the "Workshop Author"), and include it as a
form field when set:

```python
data = {}
if summary:        data["summary"] = summary
if AUTHOR:         data["author"] = AUTHOR
```

Applies to both `upload_package` (menu + `package_upload.py`) and `publish_page`.
Packages still work without it (the manifest `author` remains a server-side
fallback), but pages benefit immediately.

### 5.2 Send `path` as a form field; relax the page manifest

Server `page_publish` reads `path` from the form (`request.data.get('path')`)
and the manifest is now **optional**; it accepts **`page.toml`** (singular,
preferred) *or* `pages.toml`.

**Client work in `publish_page` / `_read_pages_toml`:**
- Send `path` as a form field on `POST /api/pages` (in addition to, or instead
  of, relying on the bundled manifest).
- Update the manifest reader to look for `page.toml` **or** `pages.toml`
  (case-insensitive), matching the server's `_ROOT_MANIFESTS`.
- Keep reading the path locally for the "This bundle publishes to path: …"
  confirmation and early-error UX — but treat a missing manifest as fine *if*
  we are sending `path` from another source (e.g. a prompt).

> Minimal viable change: keep building the ZIP exactly as today (with a manifest)
> **and** additionally send the parsed `path` as a form field. That is
> forward-compatible and needs no test-fixture changes.

### 5.3 Absolute page URL — already handled

`list_pages` / `show_page_detail` / `publish_page` do
`full = url if url.startswith("http") else f"{BASE_URL}{url}"`. With absolute
URLs the guard short-circuits, so output is correct. We may **simplify** to just
print `url`, but it is not required.

---

## 6. v11 — identity, health endpoint, rebrand

### 6.1 Connection check via `GET /api/whoami`

`connect()` currently probes `GET /api/packages` purely for its status code.
Switch it to the dedicated `GET /api/whoami`, which returns
`{organisation, organisation_name, author}` on `200` and `401` when the key is
invalid:

```python
def connect():
    session = make_session()
    r = session.get(f"{BASE_URL}/api/whoami")
    if r.status_code == 401:
        exit(1)                       # hook already printed the hint
    if r.status_code != 200:
        print(f"Could not reach the API ({r.status_code}): {r.text}")
        exit(1)
    who = r.json()
    print(f"Connected to {who.get('organisation_name')} "
          f"({who.get('organisation')}) at {BASE_URL}.\n")
    return session
```

This lets the client tell "key rejected" (`401`) from "host unreachable"
(connection error) and shows *which* workshop the key binds to. `tests/conftest`
can use the same endpoint for its skip-guard.

> `author` is `null` for an org **service** key (only per-user keys resolve a
> username) — display it only when present.

### 6.2 Rebrand strings (no behaviour change)

- Replace user-facing "Hub" wording with "Workshop"; call the credential the
  **Workshop Key** in prompts, the 401 hint, `.env.example`, and `README.md`.
- Module docstrings/comments in `api.py`/`config.py` that say "v7 server" /
  `kpf_` get refreshed.
- Endpoint paths are unchanged — no URL edits.

---

## 7. New / changed response shapes (reference)

### 7.1 Version object (`/api/packages/{name}/versions/{n}`, list, detail)
```json
{
  "version": 2,
  "author": "alice",
  "date": "2026-06-21T14:19:01Z",
  "summary": "added feature",
  "content_hash": "9f86d0818...e7cb",     // bare lowercase hex
  "deleted": false,                        // was: "tombstoned"
  "delete_reason": "",                     // was: "tombstone_reason"
  "base": {"name": "fred-chess", "version": 1}  // was: "forked_from"; null if root
}
```

### 7.2 Page object (`/api/pages`, detail, publish)
```json
{
  "path": "dev/chess24",
  "url": "https://host/pages/acme/dev/chess24/",  // now absolute
  "published_at": "2026-06-21T14:22:26Z",
  "published_by": "alice",                          // from form `author`, else user, else "service"
  "content_hash": "2cf24dba5f...9824"               // bare lowercase hex
}
```

### 7.3 `GET /api/whoami` → 200 (NEW)
```json
{ "organisation": "acme", "organisation_name": "Acme", "author": "alice" }
```

---

## 8. File-by-file change list

### `config.py`
- Add optional `AUTHOR = os.environ.get("AUTHOR")` (the Workshop Author).
- Update the `API_KEY` comment to `cel_<prefix>_<secret>` / "Workshop Key".

### `api.py`
- Extend the 401 hint with the `cel_`/`kpf_` marker change.
- Refresh the module docstring ("Workshop API", `cel_`).
- *(Optional)* startup advisory if `API_KEY` begins with `kpf_`.

### `menu.py`
- `connect()`: probe `GET /api/whoami`; print org name; keep 401/error handling.
- `show_package_detail`, `list_package_versions`: `tombstoned` → `deleted`;
  relabel `Tomb` column to `Del`.
- `show_version_detail`: `tombstoned` → `deleted` (+ `delete_reason`);
  `forked_from` → `base` (`name@version` / `none`).
- `upload_package`: send `author` form field when `AUTHOR` set.
- `publish_page` / `_read_pages_toml`: accept `page.toml` **or** `pages.toml`;
  send `path` (and `author`) as form fields.
- `set_alias` / `delete_alias`: refuse the reserved `latest` keyword.
- `download_package_version`: soften "tombstoned" wording to "deleted" on 410.
- Sweep "Hub" → "Workshop" in printed strings.

### `package_upload.py`
- Send `author` form field when `AUTHOR` set (mirrors menu upload).

### `tests/`
- `conftest.py`: use `/api/whoami` for the reachability/skip guard; the
  `published_package` teardown is unaffected (DELETE still `204`).
- `test_versions.py`: assert `deleted` (not `tombstoned`); update the 410 test
  comment; `latest` endpoint test still valid.
- New small test: `GET /api/whoami` returns `200` + an `organisation`.
- `helpers.make_page_zip`: optionally emit `page.toml` (singular) to exercise
  the preferred manifest; keep `author` line in `make_zip` (harmless fallback).

### `.env.example`, `README.md`, `README_mac_zip.md`
- `cel_…` key, *Workshop Key* / *Workshop* branding, optional `AUTHOR`,
  `page.toml` note, `whoami` connection check.

### `TDDS/`
- Add this document + `version 5 implementation plan.md`.
- Add a "Client Version 5" section to `project_design_document.md`.

---

## 9. Open questions / decisions

1. **`AUTHOR` source.** Proposed: optional `.env` value (the Workshop Author),
   sent as the `author` form field. Alternative: prompt per upload. `.env` is
   lower-friction and matches the "one identity per machine" model; chosen.
2. **Page manifest going forward.** The server accepts singular `page.toml`,
   plural `pages.toml`, or **no manifest** (when `path` is a form field). v5
   takes the conservative path: keep emitting a manifest *and* send `path` as a
   form field, accepting either filename on read. A later version can drop the
   manifest from the bundle entirely.
3. **`base` on upload.** Kept **optional** for v5 — the CLI has no install
   record to derive a base from. The read-side (`base` display) is mandatory;
   the write-side (`base_name`/`base_version`) is a nice-to-have prompt.
4. **`latest` resolution.** v5 keeps using `GET …/latest/` (still present
   server-side). Switching to client-side "highest non-deleted" computation is
   deferred — not required while the endpoint exists.
5. **Hard `kpf_` cutover.** The deployed server has **no** `kpf_` compatibility
   window, so this is an operational coordination point: the `.env` key must be
   re-issued as `cel_…` at the same time the v11 server is deployed. The client
   cannot paper over this; it can only warn early (§3).
