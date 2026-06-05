"""Shared HTTP session for the v7 (API-key) server.

Builds a ``requests.Session`` that authenticates with the per-organisation
API key (``Authorization: Api-Key kpf_...``). This replaces the old
admin-login + CSRF flow used against the pre-v7 server: with API-key auth
there is no login round-trip and no CSRF token to carry on writes.
"""
import certifi
import requests

from config import API_KEY


def _warn_on_auth_failure(response, *args, **kwargs):
    """Print a friendly hint whenever the server answers 401."""
    if response.status_code == 401:
        print(
            "  [auth] 401 Unauthorized — API key missing, invalid, revoked, "
            "or not linked to an organisation. Check API_KEY in your .env."
        )
    return response


def make_session():
    """Return a session pre-authenticated with the org API key."""
    session = requests.Session()
    session.verify = certifi.where()
    session.headers["Authorization"] = f"Api-Key {API_KEY}"
    session.hooks["response"].append(_warn_on_auth_failure)
    return session
