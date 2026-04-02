"""
Tests for auth dependencies: token extraction and user resolution.
"""

from unittest.mock import MagicMock

import pytest

from app.auth.dependencies import get_token_from_request


class TestGetTokenFromRequest:
    def test_extract_from_bearer_header(self):
        request = MagicMock()
        request.headers = {"Authorization": "Bearer my-jwt-token"}
        request.cookies = {}
        assert get_token_from_request(request) == "my-jwt-token"

    def test_extract_from_cookie(self):
        request = MagicMock()
        request.headers = {}
        request.cookies = {"access_token": "cookie-token"}
        assert get_token_from_request(request) == "cookie-token"

    def test_bearer_takes_precedence(self):
        request = MagicMock()
        request.headers = {"Authorization": "Bearer header-token"}
        request.cookies = {"access_token": "cookie-token"}
        assert get_token_from_request(request) == "header-token"

    def test_no_token_returns_none(self):
        request = MagicMock()
        request.headers = {}
        request.cookies = {}
        assert get_token_from_request(request) is None

    def test_non_bearer_auth_header_ignored(self):
        request = MagicMock()
        request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        request.cookies = {}
        assert get_token_from_request(request) is None
