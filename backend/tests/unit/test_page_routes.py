"""
Unit tests for the page routes in archer.api.page_routes.

What these routes now do
------------------------
The server-rendered pages are gone. /landing and /chat were Jinja templates,
and /chat hosted the Watson Assistant widget; both now redirect to /, which
serves the built React application behind the same login wall.

Isolation strategy
------------------
A minimal FastAPI application is assembled containing only the page router.
The real archer.app is never imported, so the lifespan handler and
verify_database() are never triggered.

Whether a frontend build exists on disk is deliberately not assumed: / returns
200 when one is present and 503 when it is not, and the authenticated test
accepts either. What matters here is the auth boundary, not the presence of a
build artefact - a test suite that fails because someone has not run npm is
testing the wrong thing.

JWT tokens are created with create_jwt_token() from archer.auth.jwt. The
JWT_SECRET_KEY is stubbed to a safe test value by backend/tests/conftest.py,
so tokens produced here validate correctly against get_current_user().

No .env file, real sales.db, IBM Cloud, watsonx, or network access is required
or permitted.
"""

import pytest

from fastapi import FastAPI
from starlette.testclient import TestClient

from archer.api import page_routes as page_routes_module
from archer.auth.jwt import create_jwt_token


# ---------------------------------------------------------------------------
# Minimal test application
# ---------------------------------------------------------------------------

def _build_test_app() -> FastAPI:
    """
    Build a minimal FastAPI application containing only the page router.
    No lifespan, no static files, no rate limiter, no archer.app side effects.
    """
    app = FastAPI()
    app.include_router(page_routes_module.router)
    return app


_test_app = _build_test_app()

_COOKIE_NAME = "archer_session"


def _client(token: str | None = None) -> TestClient:
    """A client, optionally carrying a session cookie."""
    client = TestClient(_test_app, raise_server_exceptions=False)
    client.follow_redirects = False
    if token is not None:
        client.cookies.set(_COOKIE_NAME, token)
    return client


# ---------------------------------------------------------------------------
# GET / - the application shell, behind the login wall
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_root_without_jwt_returns_401() -> None:
    """
    The application shell is not public.

    This is the load-bearing assertion of the phase that replaced the
    server-rendered pages: serving a single-page app must not have quietly
    opened a door that the Jinja pages kept shut.
    """
    response = _client().get("/")
    assert response.status_code == 401


@pytest.mark.unit
def test_root_with_valid_jwt_is_served() -> None:
    """
    A valid session gets the application shell.

    200 when a frontend build is present, 503 with an explanatory page when it
    is not. Both mean the request passed authentication, which is what this
    test is about.
    """
    response = _client(create_jwt_token("tester")).get("/")
    assert response.status_code in (200, 503)


@pytest.mark.unit
def test_root_with_tampered_jwt_returns_401() -> None:
    """A token with a corrupted signature segment is rejected."""
    token = create_jwt_token("tester")
    head, payload, signature = token.split(".")
    tampered = f"{head}.{payload}.{'A' * len(signature)}"

    response = _client(tampered).get("/")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Retired pages redirect rather than 404
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.parametrize("path", ["/landing", "/chat"])
def test_legacy_pages_redirect_to_the_app(path: str) -> None:
    """
    /landing and /chat are gone but must not 404.

    The login flow stores an intended_url cookie and sends the user back to it
    after signing in, so a stale /chat would strand a returning user on an
    error page. They redirect to / instead.
    """
    response = _client().get(path)
    assert response.status_code == 307
    assert response.headers["location"] == "/"


@pytest.mark.unit
@pytest.mark.parametrize("path", ["/landing", "/chat"])
def test_legacy_redirect_does_not_require_auth(path: str) -> None:
    """
    The redirect itself is unauthenticated, and deliberately so.

    Redirecting is not disclosure: the destination enforces the login wall.
    Requiring auth to be told where a page moved to would send an
    unauthenticated visitor to /login without ever recording where they were
    trying to go.
    """
    response = _client().get(path)
    assert response.status_code == 307
