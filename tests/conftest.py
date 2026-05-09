import os
import sys
import uuid
from urllib.parse import quote

import certifi
import pytest
import requests

# Make project root importable (so `from config import ...` works from tests).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import BASE_URL, USERNAME, PASSWORD  # noqa: E402

from .helpers import make_zip  # noqa: E402


def _csrf(session):
    return session.cookies.get("csrftoken")


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.verify = certifi.where()
    s.auth = (USERNAME, PASSWORD)

    try:
        s.get(f"{BASE_URL}/admin/login/", timeout=5)
    except requests.exceptions.RequestException as exc:
        pytest.skip(f"Server not reachable at {BASE_URL}: {exc}")

    r = s.post(
        f"{BASE_URL}/admin/login/",
        data={
            "username": USERNAME,
            "password": PASSWORD,
            "csrfmiddlewaretoken": _csrf(s),
            "next": "/admin/",
        },
    )
    if "Log in" in r.text:
        pytest.skip("Login failed — check .env credentials")
    return s


@pytest.fixture
def fresh_package_name():
    """Unique unused package name. Caller owns creation/cleanup."""
    return f"pytest-{uuid.uuid4().hex[:12]}"


@pytest.fixture
def published_package(session, fresh_package_name):
    """A package with one published version (v1). Cascade-deleted on teardown."""
    name = fresh_package_name
    r = session.post(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/",
        files={"file": (f"{name}.zip", make_zip(name, "v1"), "application/zip")},
        data={"summary": "test fixture v1"},
        headers={"X-CSRFToken": _csrf(session)},
    )
    assert r.status_code in (200, 201), f"fixture publish failed: {r.status_code} {r.text}"

    yield name

    # Teardown: cascade-delete. Lenient — any prior tombstoning during the test is fine.
    try:
        session.delete(
            f"{BASE_URL}/api/packages/{quote(name, safe='')}/",
            json={"reason": "test teardown"},
            headers={"X-CSRFToken": _csrf(session)},
        )
    except requests.exceptions.RequestException:
        pass
