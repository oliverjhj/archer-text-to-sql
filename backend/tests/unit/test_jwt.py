"""
Unit tests for JWT token creation and verification in archer.auth.jwt.

Tests the actual behaviour of create_jwt_token() and verify_jwt_token():
  - A created token contains the expected payload fields (sub, exp, iat).
  - A valid token is verified and its payload is returned.
  - A token with a tampered signature is rejected (returns None).
  - An arbitrary non-JWT string is rejected (returns None).
  - An empty string is rejected (returns None).
  - A token whose exp claim is in the past is rejected (returns None).

Safe stub secrets are supplied by backend/tests/conftest.py via
os.environ.setdefault() before any test module is imported.
JWT_SECRET_KEY is read at archer.auth.jwt import time; the stub value
is in place before that happens.

No .env file, no real sales.db, no IBM Cloud or watsonx services are
required or contacted by any test in this file.
"""

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from archer.auth.jwt import (
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    JWT_SECRET_KEY,
    create_jwt_token,
    verify_jwt_token,
)


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_create_jwt_token_contains_sub() -> None:
    """Created token payload contains the correct 'sub' claim."""
    token = create_jwt_token("testuser")
    payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == "testuser"


@pytest.mark.unit
def test_create_jwt_token_contains_exp() -> None:
    """Created token payload contains an 'exp' claim."""
    token = create_jwt_token("testuser")
    payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert "exp" in payload


@pytest.mark.unit
def test_create_jwt_token_contains_iat() -> None:
    """Created token payload contains an 'iat' claim."""
    token = create_jwt_token("testuser")
    payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert "iat" in payload


@pytest.mark.unit
def test_create_jwt_token_exp_is_approximately_24_hours_ahead() -> None:
    """The 'exp' claim is approximately JWT_EXPIRATION_HOURS hours in the future."""
    before = datetime.now(UTC)
    token = create_jwt_token("testuser")
    after = datetime.now(UTC)

    payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    exp_dt = datetime.fromtimestamp(payload["exp"], UTC)

    expected_low = before + timedelta(hours=JWT_EXPIRATION_HOURS) - timedelta(seconds=5)
    expected_high = after + timedelta(hours=JWT_EXPIRATION_HOURS) + timedelta(seconds=5)

    assert expected_low <= exp_dt <= expected_high


# ---------------------------------------------------------------------------
# Token verification — valid token
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_verify_jwt_token_returns_payload_for_valid_token() -> None:
    """verify_jwt_token() returns the decoded payload dict for a freshly created token."""
    token = create_jwt_token("alice")
    payload = verify_jwt_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"


# ---------------------------------------------------------------------------
# Token verification — rejection cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_verify_jwt_token_returns_none_for_tampered_signature() -> None:
    """A token whose signature segment has been replaced is rejected."""
    token = create_jwt_token("alice")
    # JWT tokens are three dot-separated base64url segments: header.payload.signature
    # Replacing the signature segment produces an invalid token.
    parts = token.split(".")
    parts[-1] = "invalidsignatureXXXXXXXXXXXXXXXXXXXXXXXXXX"
    tampered = ".".join(parts)
    assert verify_jwt_token(tampered) is None


@pytest.mark.unit
def test_verify_jwt_token_returns_none_for_arbitrary_string() -> None:
    """An arbitrary string that is not a JWT is rejected."""
    assert verify_jwt_token("not-a-jwt-token-at-all") is None


@pytest.mark.unit
def test_verify_jwt_token_returns_none_for_empty_string() -> None:
    """An empty string is not a valid token and must be rejected."""
    assert verify_jwt_token("") is None


@pytest.mark.unit
def test_verify_jwt_token_returns_none_for_expired_token() -> None:
    """A token whose 'exp' claim is in the past is rejected (ExpiredSignatureError caught)."""
    # Build a token manually using the same stub secret and algorithm so that the
    # signature is valid, but set exp to one hour in the past.  This exercises the
    # jwt.ExpiredSignatureError path inside verify_jwt_token() without relying on
    # time.sleep() or monkey-patching datetime.
    expired_payload = {
        "sub": "expireduser",
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "iat": datetime.now(UTC) - timedelta(hours=2),
    }
    expired_token = pyjwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    assert verify_jwt_token(expired_token) is None
