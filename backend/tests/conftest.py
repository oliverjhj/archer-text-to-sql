"""
Shared pytest configuration for the Archer test suite.

Isolation strategy
------------------
Stub values for JWT_SECRET_KEY, CSRF_SECRET_KEY, and WEBHOOK_SECRET are
injected via os.environ.setdefault() so that modules which read these
variables at import time (e.g. archer.auth.jwt) receive a safe, non-None
value without requiring a .env file.

Cloud and LLM environment variables (IBM_API_KEY, PROJECT_ID, COS_API_KEY_ID,
COS_INSTANCE_CRN, COS_ENDPOINT, BUCKET_NAME, DB_FILE_NAME) are intentionally
absent from this file.  Any test that accidentally reaches a live service will
fail loudly rather than silently pass.
"""

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-stub-not-for-production")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-stub-not-for-production")
os.environ.setdefault("WEBHOOK_SECRET", "test-webhook-secret-stub-not-for-production")
