import io
import zipfile
from urllib.parse import quote

from config import BASE_URL

from .helpers import make_zip


def test_list_versions(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/versions/"
    )
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) >= 1
    assert any(v.get("version") == 1 for v in versions)


def test_show_single_version(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/versions/1/"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == 1
    assert data.get("author")


def test_show_unknown_version_404(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/versions/999/"
    )
    assert r.status_code == 404


def test_publish_second_version(session, published_package):
    name = published_package
    r = session.post(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/",
        files={"file": (f"{name}.zip", make_zip(name, "v2"), "application/zip")},
        data={"summary": "second publish"},
        headers={"X-CSRFToken": session.cookies.get("csrftoken")},
    )
    assert r.status_code in (200, 201), r.text
    assert r.json()["version"] == 2


def test_publish_implicit_register(session, fresh_package_name):
    """POST /versions/ on a non-existent package should implicitly register it."""
    name = fresh_package_name
    r = session.post(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/",
        files={"file": (f"{name}.zip", make_zip(name), "application/zip")},
        data={"summary": "implicit register"},
        headers={"X-CSRFToken": session.cookies.get("csrftoken")},
    )
    assert r.status_code in (200, 201), r.text

    r = session.get(f"{BASE_URL}/api/packages/{quote(name, safe='')}/")
    assert r.status_code == 200

    # Cleanup
    session.delete(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/",
        headers={"X-CSRFToken": session.cookies.get("csrftoken")},
    )


def test_download_specific_version(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/versions/1/download/"
    )
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert "package.toml" in z.namelist()


def test_download_latest(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/latest/"
    )
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert "package.toml" in z.namelist()


def test_tombstone_version_returns_410_on_download(session, published_package):
    name = published_package

    # Publish v2 so we can tombstone it (don't kill the only version)
    r = session.post(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/",
        files={"file": (f"{name}.zip", make_zip(name, "v2"), "application/zip")},
        data={"summary": "to be tombstoned"},
        headers={"X-CSRFToken": session.cookies.get("csrftoken")},
    )
    assert r.status_code in (200, 201)

    r = session.delete(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/2/",
        json={"reason": "test"},
        headers={"X-CSRFToken": session.cookies.get("csrftoken")},
    )
    assert r.status_code in (200, 204), r.text

    # Subsequent download of v2 should be 410 Gone
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/2/download/"
    )
    assert r.status_code == 410
