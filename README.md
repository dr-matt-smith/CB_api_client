# celbridge-hub-api-client

Client to connect to Celbridge-hub API for ZIPed package upload and download
- (see **celbridge-hub** package API server: https://github.com/celbridge-org/celbridge-hub)

> **v2 client** — targets the **v7** server (per-organisation isolation).
> Authentication is via an **API key**; the old admin-login/password flow is gone.

## setup - create `.env`

Create a `.env` with the server URL and your organisation **API key**:

```
BASE_URL=https://yourusername.pythonanywhere.com
API_KEY=kpf_xxxxxxxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The API key is issued **once** by your organisation admin (it is stored only as a
salted hash on the server, so it cannot be recovered later — keep it safe). Every
request the client makes sends `Authorization: Api-Key <key>`; there is no separate
login step. See `.env.example` for a template.

## CLI menu script

An interactive menu makes it easy to browse packages, upload new versions from the
`files_to_upload/` directory, download to `downloads/`, manage aliases, and publish
web pages.

Single-file uploads (the old `upload.py` / `/api/upload/`) were removed in v7.
To upload, use the menu's **Upload** option or `package_upload.py`.

### top-level menu

```bash
    % python menu.py

    Connected to https://yourusername.pythonanywhere.com with API key.

    === Packages API ===
      1 - Packages    (list / show / register / delete)
      2 - Versions    (list / detail / upload / download / tombstone)
      3 - Aliases     (list / set / remove)
      4 - History     (full / as-of-version)
      5 - Pages       (publish / unpublish / status / history)
      6 - Download latest version        (GET  /api/packages/{name}/latest)
      7 - Upload a package               (POST /api/packages/{name}/versions)
      0 - Exit

    Select option:
```

### example: listing and inspecting packages

```bash
    Select option: 1

    --- Packages ---
      1 - List all packages              (GET    /api/packages)
      2 - Show package metadata          (GET    /api/packages/{name})
      3 - Register a new (empty) package (POST   /api/packages)
      4 - Delete entire package          (DELETE /api/packages/{name})
      0 - Back

    Select option: 1
      GET https://yourusername.pythonanywhere.com/api/packages/

    Name                            Latest  Vers  Author               Uploaded
    ------------------------------------------------------------------------------------------
    fred-chess                           2     2  popeye               2026-05-09 14:19:01
    space-chess24                        1     1  chris                2026-05-09 14:22:26

    Select option: 2
    ...
    Enter number (or press Enter to cancel): 1
      GET https://yourusername.pythonanywhere.com/api/packages/fred-chess/

    Package: fred-chess
    Created: 2026-05-09 14:11:38

     Ver  Author               Uploaded               Tomb  Summary
    ------------------------------------------------------------------------------------------
       2  popeye               2026-05-09 14:19:01          added feature - should become version 2
       1  mattilda             2026-05-09 14:11:38          forked to create new package fred-chess

    Alias                Version
    ------------------------------
    latest                     2
```

### example: publishing a web page

Publishing serves the **latest** version's `public/` subfolder to
`/pages/<org-slug>/<name>/`. (Tombstoning the published version auto-unpublishes it.)

```bash
    Select option: 5

    --- Pages / Publish ---
      (publish serves the LATEST version's public/ folder to /pages/<org>/<name>/;
       tombstoning the published version auto-unpublishes it)
      1 - Publish latest version         (POST   /api/publish/{name})
      2 - Unpublish a package            (DELETE /api/publish/{name})
      3 - Show current publication       (GET    /api/publish/{name})
      4 - Show publication history       (GET    /api/publish/{name}/history)
      0 - Back

    Select option: 1
      POST https://yourusername.pythonanywhere.com/api/publish/mysite
    Published: mysite v2
      Page: https://yourusername.pythonanywhere.com/pages/acme/mysite/
```

## uploading from the command line

`package_upload.py` uploads a single package ZIP (must contain `package.toml` with a
`name`):

```bash
  python package_upload.py ./files_to_upload/mysite.zip --summary "my change"
```

## running the tests

The tests are live integration tests — they run against the server in `BASE_URL`
using the `API_KEY` from `.env` (and skip if the server is unreachable or the key is
rejected):

```bash
  pip install -r requirements-dev.txt
  pytest -q
```
