"""Tests for the v11 identity endpoint (/api/whoami).

Returns {organisation, organisation_name, author} on 200 when the Workshop Key
is valid, and 401 when it is not. The client uses it for the connection check
and to show which workshop the key binds to.
"""
from config import BASE_URL


def test_whoami_returns_organisation(session):
    r = session.get(f"{BASE_URL}/api/whoami")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("organisation")
    # author is null for an org service key; only assert the key is present.
    assert "author" in data
