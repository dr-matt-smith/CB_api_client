import os
import sys
import uuid
from urllib.parse import quote

import pytest
import requests

# Make project root importable (so `from config import ...` works from tests).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import BASE_URL  # noqa: E402
from api import make_session  # noqa: E402

from .helpers import make_zip  # noqa: E402


@pytest.fixture(scope="session")
def session():
    """Authenticated session using the v7 org API key (no admin login / CSRF)."""
    s = make_session()
    try:
        r = s.get(f"{BASE_URL}/api/packages", timeout=5)
    except requests.exceptions.RequestException as exc:
        pytest.skip(f"Server not reachable at {BASE_URL}: {exc}")
    if r.status_code == 401:
        pytest.skip("API key rejected — check API_KEY in .env")
    if r.status_code != 200:
        pytest.skip(f"Unexpected status from /api/packages: {r.status_code}")
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
    )
    assert r.status_code in (200, 201), f"fixture publish failed: {r.status_code} {r.text}"

    yield name

    # Teardown: cascade-delete. Lenient — any prior tombstoning during the test is fine.
    try:
        session.delete(
            f"{BASE_URL}/api/packages/{quote(name, safe='')}/",
            json={"reason": "test teardown"},
        )
    except requests.exceptions.RequestException:
        pass


@pytest.fixture
def published_page_package(session, fresh_package_name):
    """A package whose v1 contains a public/ folder (publishable). Cleaned up on teardown."""
    name = fresh_package_name
    r = session.post(
        f"{BASE_URL}/api/packages/{quote(name, safe='')}/versions/",
        files={
            "file": (f"{name}.zip", make_zip(name, "v1", with_public=True), "application/zip")
        },
        data={"summary": "page fixture v1"},
    )
    assert r.status_code in (200, 201), f"fixture publish failed: {r.status_code} {r.text}"

    yield name

    # Best-effort: unpublish (ignore if not published) then cascade-delete.
    try:
        session.delete(f"{BASE_URL}/api/publish/{quote(name, safe='')}")
    except requests.exceptions.RequestException:
        pass
    try:
        session.delete(
            f"{BASE_URL}/api/packages/{quote(name, safe='')}/",
            json={"reason": "test teardown"},
        )
    except requests.exceptions.RequestException:
        pass
