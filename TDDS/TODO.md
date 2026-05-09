TODO
====

Known gaps / follow-ups for the test suite added in version 3.

1. Tests cover the API, not the menu UI
-----------------------------------------
The pytest suite under `tests/` hits each endpoint directly via `requests` —
it verifies the API contract that `menu.py` depends on, but it does **not**
exercise the menu functions themselves (which read `input()` and write
`print()`).

That means none of the following is covered today:
- top-level menu navigation (Packages / Versions / Aliases / History / latest)
- sub-menu back/exit handling
- input parsing (numeric pick → package name, version-number prompts, y/N
  confirmations, alias-name prompts)
- output formatting (column widths, headers, the per-call `GET <url>` echo,
  the post-upload `download_url` / `public_url` print)
- error UX (e.g. invalid pick, blank input cancels, tombstoned download
  surfaces 410 cleanly)

If we want to harden the menu itself, add a separate `tests/test_menu.py`
that drives the menu functions with `monkeypatch` on `builtins.input` and
captures stdout via `capsys`. Keep it shallow — verify routing and
prompt-handling, not endpoint behaviour (already covered).


2. Orphan packages possible on partial test failure
---------------------------------------------------
The `published_package` fixture in `tests/conftest.py` cleans up cleanly
because the cascade-delete runs in fixture teardown regardless of test
outcome.

But several tests create packages **outside** the fixture and clean up
inline at the end of the test body:
- `test_packages.py::test_register_show_delete`
- `test_packages.py::test_register_duplicate_returns_409`
- `test_versions.py::test_publish_implicit_register`

If any of these fails part-way through, the `session.delete(...)` at the
bottom never runs and the package is left on the server. Names are unique
(`pytest-<uuid>`) so they won't collide with anything real, but they will
accumulate over repeated failed runs.

Two ways to fix:
- Move those teardowns into the fixture by giving each test its own
  fixture variant (e.g. `registered_package` that registers via POST
  `/api/packages/` and tears down). Cleanest, but adds fixtures.
- Wrap the body in `try` / `finally` so the inline cleanup always runs.
  Smaller change, slightly noisier tests.

Optional safety net: a session-scoped autouse teardown that lists all
packages and cascade-deletes any whose name starts with `pytest-`. Belt
and braces, but useful in CI.
