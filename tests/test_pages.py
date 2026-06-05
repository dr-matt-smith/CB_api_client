"""Tests for the v8 standalone Pages API (/api/pages).

Pages are fully decoupled from packages: each page is its own ZIP upload that
contains a pages.toml with [publish].path, served at /pages/<org>/<path>/.
"""
from urllib.parse import quote

import requests

from config import BASE_URL

from .helpers import make_page_zip, make_zip


def test_published_page_is_served(session, published_page):
    """The served page is reachable publicly (no auth) and contains its content."""
    path = published_page
    r = session.get(f"{BASE_URL}/api/pages/{quote(path, safe='/')}")
    assert r.status_code == 200, r.text
    url = r.json()["url"]
    full = url if url.startswith("http") else f"{BASE_URL}{url}"

    # Pages are public — fetch without the API key.
    page = requests.get(full)
    assert page.status_code == 200, f"{full} -> {page.status_code}"
    # make_page_zip writes index.html containing the path (used as the marker).
    assert path in page.text


def test_page_lifecycle(session, page_path):
    """Publish → list → detail → unpublish → gone."""
    path = page_path
    zip_name = f"{path.replace('/', '_')}.zip"

    # POST → publish from the bundle's own ZIP
    r = session.post(
        f"{BASE_URL}/api/pages",
        files={"file": (zip_name, make_page_zip(path), "application/zip")},
    )
    assert r.status_code in (200, 201), r.text
    data = r.json()
    assert data["path"] == path
    assert data["url"]

    # GET list → the page is present
    r = session.get(f"{BASE_URL}/api/pages")
    assert r.status_code == 200
    assert any(p.get("path") == path for p in r.json())

    # GET detail → matches
    r = session.get(f"{BASE_URL}/api/pages/{quote(path, safe='/')}")
    assert r.status_code == 200
    assert r.json()["path"] == path

    # DELETE → unpublish
    r = session.delete(f"{BASE_URL}/api/pages/{quote(path, safe='/')}")
    assert r.status_code in (200, 204), r.text

    # GET detail → no longer published
    r = session.get(f"{BASE_URL}/api/pages/{quote(path, safe='/')}")
    assert r.status_code == 404


def test_publish_missing_pages_toml_422(session, fresh_package_name):
    """A ZIP with no pages.toml is rejected by the pages endpoint."""
    # Reuse make_zip — it produces a package.toml bundle, no pages.toml.
    r = session.post(
        f"{BASE_URL}/api/pages",
        files={"file": ("no-manifest.zip", make_zip(fresh_package_name), "application/zip")},
    )
    assert r.status_code == 422, r.text


def test_page_detail_unpublished_404(session, page_path):
    """A path that was never published has no current publication."""
    r = session.get(f"{BASE_URL}/api/pages/{quote(page_path, safe='/')}")
    assert r.status_code == 404


def test_publish_path_overlap_409(session, published_page):
    """A path that strictly contains an existing page's path is rejected."""
    child = f"{published_page}/beta"
    r = session.post(
        f"{BASE_URL}/api/pages",
        files={"file": ("overlap.zip", make_page_zip(child), "application/zip")},
    )
    assert r.status_code == 409, r.text
    # Clean up if the server unexpectedly accepted it.
    if r.status_code in (200, 201):
        session.delete(f"{BASE_URL}/api/pages/{quote(child, safe='/')}")


def test_pages_independent_of_packages(session, published_package, page_path):
    """Decoupling: deleting a package does not affect a separately-published page."""
    path = page_path
    r = session.post(
        f"{BASE_URL}/api/pages",
        files={"file": ("indep.zip", make_page_zip(path), "application/zip")},
    )
    assert r.status_code in (200, 201), r.text
    try:
        # Cascade-delete the unrelated package.
        session.delete(
            f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/",
            json={"reason": "decoupling test"},
        )
        # The page is untouched.
        r = session.get(f"{BASE_URL}/api/pages/{quote(path, safe='/')}")
        assert r.status_code == 200, r.text
        assert r.json()["path"] == path
    finally:
        session.delete(f"{BASE_URL}/api/pages/{quote(path, safe='/')}")
