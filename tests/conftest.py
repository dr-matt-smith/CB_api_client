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

from .helpers import make_zip, make_page_zip  # noqa: E402


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
def page_path():
    """Unique unused page publish path. Caller owns publish/cleanup."""
    return f"pytest-pages/{uuid.uuid4().hex[:12]}"


@pytest.fixture
def published_page(session, page_path):
    """A live page published from its own ZIP (v8 /api/pages). Unpublished on teardown."""
    path = page_path
    r = session.post(
        f"{BASE_URL}/api/pages",
        files={
            "file": (
                f"{path.replace('/', '_')}.zip",
                make_page_zip(path, marker=path),
                "application/zip",
            )
        },
    )
    assert r.status_code in (200, 201), f"fixture page publish failed: {r.status_code} {r.text}"

    yield path

    # Teardown: unpublish (best-effort; fine if a test already removed it).
    try:
        session.delete(f"{BASE_URL}/api/pages/{quote(path, safe='/')}")
    except requests.exceptions.RequestException:
        pass
