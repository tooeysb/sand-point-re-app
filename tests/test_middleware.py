"""
Tests for middleware: SSO and Correlation ID.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.request_context import get_request_id, set_request_id


# ── Request Context ──────────────────────────────────────────────────────────


class TestRequestContext:
    def test_set_and_get_request_id(self):
        rid = set_request_id("abc123")
        assert rid == "abc123"
        assert get_request_id() == "abc123"

    def test_auto_generate_request_id(self):
        rid = set_request_id(None)
        assert rid is not None
        assert len(rid) == 12  # uuid hex[:12]

    def test_overwrite_request_id(self):
        set_request_id("first")
        set_request_id("second")
        assert get_request_id() == "second"


# ── SSO Middleware ────────────────────────────────────────────────────────────


class TestSSOMiddleware:
    def test_public_prefixes_constant(self):
        """Verify expected public paths are in the list."""
        from app.middleware.sso import PUBLIC_PREFIXES

        assert "/health" in PUBLIC_PREFIXES
        assert "/api/auth/sso" in PUBLIC_PREFIXES
        assert "/static" in PUBLIC_PREFIXES
        assert "/auth/login" in PUBLIC_PREFIXES


# ── Correlation ID Middleware ─────────────────────────────────────────────────


class TestCorrelationIDMiddleware:
    def test_request_id_is_12_chars(self):
        rid = set_request_id()
        assert len(rid) == 12

    def test_client_provided_id_preserved(self):
        """Client-provided X-Request-ID should be used as-is."""
        rid = set_request_id("client-provided-id-12345")
        assert rid == "client-provided-id-12345"
