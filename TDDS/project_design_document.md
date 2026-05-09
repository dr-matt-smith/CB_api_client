


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

