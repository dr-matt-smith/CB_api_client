from urllib.parse import quote

import requests

from config import BASE_URL


def test_published_page_is_served(session, published_page_package):
    """The served directory URL returns the public/index.html (server falls back
    to index.html for a directory request)."""
    name = published_page_package
    base = f"{BASE_URL}/api/publish/{quote(name, safe='')}"

    r = session.post(base)
    assert r.status_code == 200, r.text
    url = r.json()["url"]
    full = url if url.startswith("http") else f"{BASE_URL}{url}"

    # Pages are public — fetch without auth, hitting the bare directory (no index.html).
    page = requests.get(full)
    assert page.status_code == 200, f"{full} -> {page.status_code}"
    # make_zip writes public/index.html containing the package name in an <h1>.
    assert name in page.text


def test_publish_lifecycle(session, published_page_package):
    name = published_page_package
    base = f"{BASE_URL}/api/publish/{quote(name, safe='')}"

    # POST → publish latest version's public/ folder
    r = session.post(base)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["package"] == name
    assert data["version"] == 1
    assert data["url"]

    # GET → currently published
    r = session.get(base)
    assert r.status_code == 200
    assert r.json()["version"] == 1

    # GET history → includes the publish event
    r = session.get(f"{base}/history")
    assert r.status_code == 200
    assert any(e.get("action") == "publish" for e in r.json())

    # DELETE → unpublish
    r = session.delete(base)
    assert r.status_code in (200, 204), r.text

    # GET → no longer published
    r = session.get(base)
    assert r.status_code == 404

    # GET history → now includes the unpublish event too
    r = session.get(f"{base}/history")
    assert r.status_code == 200
    actions = {e.get("action") for e in r.json()}
    assert "publish" in actions
    assert "unpublish" in actions


def test_publish_without_public_folder_422(session, published_package):
    """published_package's v1 has no public/ folder, so publish must 422."""
    name = published_package
    r = session.post(f"{BASE_URL}/api/publish/{quote(name, safe='')}")
    assert r.status_code == 422, r.text


def test_publish_status_unpublished_404(session, published_package):
    """A package that was never published has no current publication."""
    name = published_package
    r = session.get(f"{BASE_URL}/api/publish/{quote(name, safe='')}")
    assert r.status_code == 404
