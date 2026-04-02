"""
Tests for core modules: errors, logging, request context, and config.
"""

import json
import logging
from unittest.mock import patch

import pytest

from app.core.request_context import get_request_id, set_request_id


# ── Error Handling ───────────────────────────────────────────────────────────


class TestErrorResponse:
    def test_error_response_structure(self):
        from app.core.errors import _error_response

        response = _error_response(400, "BAD_REQUEST", "Something went wrong")
        assert response.status_code == 400
        body = json.loads(response.body.decode())
        assert "error" in body
        assert body["error"]["code"] == "BAD_REQUEST"
        assert body["error"]["message"] == "Something went wrong"

    def test_error_response_includes_request_id(self):
        from app.core.errors import _error_response

        set_request_id("test-req-id")
        response = _error_response(500, "INTERNAL_ERROR", "Oops")
        body = json.loads(response.body.decode())
        assert body["error"]["request_id"] == "test-req-id"

    def test_error_response_no_request_id(self):
        from app.core.errors import _error_response

        set_request_id(None)  # This generates a new one, but let's test with explicit
        # We can't easily clear the contextvar, but at minimum the response should work
        response = _error_response(404, "NOT_FOUND", "Not found")
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "NOT_FOUND"


# ── Logging ──────────────────────────────────────────────────────────────────


class TestLogging:
    def test_redact_password(self):
        from app.core.logging import _redact

        msg = "connecting with password=s3cr3t&user=admin"
        redacted = _redact(msg)
        assert "s3cr3t" not in redacted
        assert "REDACTED" in redacted

    def test_redact_bearer_token(self):
        from app.core.logging import _redact

        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.xxx"
        redacted = _redact(msg)
        assert "eyJ" not in redacted
        assert "REDACTED" in redacted

    def test_redact_connection_string(self):
        from app.core.logging import _redact

        msg = "postgres://user:secretpass@host:5432/db"
        redacted = _redact(msg)
        assert "secretpass" not in redacted

    def test_redact_preserves_clean_message(self):
        from app.core.logging import _redact

        msg = "Processing 42 items in batch"
        assert _redact(msg) == msg

    def test_get_logger_returns_logger(self):
        from app.core.logging import get_logger

        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    @patch.dict("os.environ", {"APP_ENV": "production"})
    def test_json_formatter_output(self):
        from app.core.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"


# ── Config ───────────────────────────────────────────────────────────────────


class TestConfig:
    def test_settings_defaults(self):
        from app.config import Settings

        s = Settings()
        assert s.jwt_algorithm == "HS256"
        assert s.jwt_access_token_expire_minutes == 30
        assert s.debug is False

    def test_settings_app_name(self):
        from app.config import Settings

        s = Settings()
        assert "Sand Point" in s.app_name


# ── DB Models ────────────────────────────────────────────────────────────────


class TestDBModels:
    def test_user_role_enum(self):
        from app.db.models import UserRole

        assert UserRole.admin.value == "admin"
        assert UserRole.user.value == "user"

    def test_generate_uuid(self):
        from app.db.models import generate_uuid

        u1 = generate_uuid()
        u2 = generate_uuid()
        assert isinstance(u1, str)
        assert u1 != u2
        assert len(u1) == 36  # Standard UUID format
