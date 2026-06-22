"""Shared HTTP session for the Celbridge Workshop API (API-key auth).

Builds a ``requests.Session`` that authenticates with the per-organisation
Workshop Key (``Authorization: Api-Key cel_...``). This replaces the old
admin-login + CSRF flow: with API-key auth there is no login round-trip and
no CSRF token to carry on writes.

The v11 server requires keys to start with the ``cel_`` marker; older
``kpf_`` keys are rejected outright (no compatibility window) and must be
re-issued.
"""
import certifi
import requests

from config import API_KEY


def _warn_on_auth_failure(response, *args, **kwargs):
    """Print a friendly hint whenever the server answers 401."""
    if response.status_code == 401:
        print(
            "  [auth] 401 Unauthorized — Workshop Key missing, invalid, revoked, "
            "or not linked to an organisation. Check API_KEY in your .env. "
            "Note: v11 keys start with `cel_`; old `kpf_` keys are rejected — re-issue."
        )
    return response


def make_session():
    """Return a session pre-authenticated with the org Workshop Key."""
    if API_KEY.startswith("kpf_"):
        print(
            "  [auth] Warning: API_KEY starts with `kpf_`, which the v11 Workshop "
            "server rejects. Re-issue it as a `cel_…` Workshop Key in your .env."
        )
    session = requests.Session()
    session.verify = certifi.where()
    session.headers["Authorization"] = f"Api-Key {API_KEY}"
    session.hooks["response"].append(_warn_on_auth_failure)
    return session
