import os
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY", "fallback-secret-key-change-in-production")
csrf_serializer = URLSafeTimedSerializer(CSRF_SECRET_KEY)

def generate_csrf_token() -> str:
    """Generate a cryptographically signed CSRF token with 1-hour expiration"""
    return csrf_serializer.dumps("csrf_token", salt="csrf-protection")

def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token signature and expiration (1 hour max age)"""
    try:
        csrf_serializer.loads(token, salt="csrf-protection", max_age=3600)
        return True
    except (SignatureExpired, BadSignature):
        return False

