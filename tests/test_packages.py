import uuid
from urllib.parse import quote

from config import BASE_URL


def test_list_packages(session):
    r = session.get(f"{BASE_URL}/api/packages/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_register_show_delete(session, fresh_package_name):
    name = fresh_package_name

    # POST /api/packages/  → register
    r = session.post(f"{BASE_URL}/api/packages/", json={"name": name})
    assert r.status_code == 201, r.text

    # GET /api/packages/{name}/  → metadata
    r = session.get(f"{BASE_URL}/api/packages/{quote(name, safe='')}/")
    assert r.status_code == 200
    payload = r.json()
    assert payload.get("name") == name

    # DELETE /api/packages/{name}/  → cascade-tombstone
    r = session.delete(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/",
        json={"reason": "test cleanup"},
    )
    assert r.status_code in (200, 204), r.text


def test_register_duplicate_returns_409(session, fresh_package_name):
    name = fresh_package_name

    r = session.post(f"{BASE_URL}/api/packages/", json={"name": name})
    assert r.status_code == 201

    r = session.post(f"{BASE_URL}/api/packages/", json={"name": name})
    assert r.status_code == 409

    # Cleanup
    session.delete(f"{BASE_URL}/api/packages/{quote(name, safe='')}/")


def test_show_unknown_package_404(session):
    name = f"does-not-exist-{uuid.uuid4().hex[:8]}"
    r = session.get(f"{BASE_URL}/api/packages/{quote(name, safe='')}/")
    assert r.status_code == 404


def test_show_published_package_metadata(session, published_package):
    r = session.get(f"{BASE_URL}/api/packages/{quote(published_package, safe='')}/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == published_package
    versions = data.get("versions", [])
    assert any(v.get("version") == 1 for v in versions)
