from urllib.parse import quote

from config import BASE_URL

from .helpers import make_zip


def test_full_package_history(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/history/"
    )
    assert r.status_code == 200
    assert "Version 1" in r.text


def test_version_history_as_of_v1(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/versions/1/history/"
    )
    assert r.status_code == 200
    assert "Version 1" in r.text


def test_version_history_unknown_returns_404(session, published_package):
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/versions/999/history/"
    )
    assert r.status_code == 404


def test_version_history_omits_versions_above_n(session, published_package):
    name = published_package

    # Publish v2 so we have something past the as-of point
    r = session.post(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/",
        files={"file": (f"{name}.zip", make_zip(name, "v2"), "application/zip")},
        data={"summary": "v2 for as-of test"},
    )
    assert r.status_code in (200, 201)

    # As-of v1: must NOT contain "Version 2"
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/1/history/"
    )
    assert r.status_code == 200
    assert "Version 1" in r.text
    assert "Version 2" not in r.text

    # As-of v2: must contain both
    r = session.get(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/2/history/"
    )
    assert r.status_code == 200
    assert "Version 1" in r.text
    assert "Version 2" in r.text
