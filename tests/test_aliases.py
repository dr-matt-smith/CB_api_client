from urllib.parse import quote

from config import BASE_URL


def test_alias_lifecycle(session, published_package):
    name = published_package
    base = f"{BASE_URL}/api/packages/{quote(name, safe='')}"

    # GET aliases (should succeed even when empty / only-server-managed)
    r = session.get(f"{base}/aliases/")
    assert r.status_code == 200

    # PUT alias "stable" → v1
    r = session.put(
        f"{base}/aliases/stable/",
        json={"version": 1},
        headers={"X-CSRFToken": session.cookies.get("csrftoken")},
    )
    assert r.status_code in (200, 201), r.text

    # GET aliases — should now include "stable"
    r = session.get(f"{base}/aliases/")
    assert r.status_code == 200
    aliases = r.json()
    by_name = {a.get("name"): a for a in aliases}
    assert "stable" in by_name
    assert by_name["stable"].get("version") == 1

    # DELETE alias
    r = session.delete(
        f"{base}/aliases/stable/",
        headers={"X-CSRFToken": session.cookies.get("csrftoken")},
    )
    assert r.status_code in (200, 204), r.text

    # GET aliases — "stable" should be gone
    r = session.get(f"{base}/aliases/")
    aliases = r.json()
    assert "stable" not in {a.get("name") for a in aliases}
