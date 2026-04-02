"""
Tests for authentication modules: JWT, password hashing, and token utilities.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiry,
)
from app.auth.password import hash_password, verify_password
from app.auth.tokens import (
    generate_token,
    generate_token_pair,
    hash_token,
    verify_token_hash,
)


# ── JWT Token Creation & Validation ──────────────────────────────────────────


class TestJWT:
    def test_create_and_decode_access_token(self):
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        data = {"sub": "user-456"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"

    def test_access_token_expires(self):
        data = {"sub": "user-123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)
        assert payload is None  # Expired token should return None

    def test_refresh_token_custom_expiry(self):
        data = {"sub": "user-123"}
        token = create_refresh_token(data, expires_delta=timedelta(hours=1))
        payload = decode_token(token)
        assert payload is not None

    def test_decode_invalid_token(self):
        assert decode_token("not-a-real-jwt") is None

    def test_decode_tampered_token(self):
        data = {"sub": "user-123"}
        token = create_access_token(data)
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_get_token_expiry(self):
        data = {"sub": "user-123"}
        token = create_access_token(data)
        expiry = get_token_expiry(token)
        assert expiry is not None
        assert isinstance(expiry, datetime)
        assert expiry > datetime.utcnow()

    def test_get_token_expiry_invalid(self):
        assert get_token_expiry("invalid") is None

    def test_token_preserves_extra_data(self):
        data = {"sub": "user-123", "role": "admin", "email": "a@b.com"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload["role"] == "admin"
        assert payload["email"] == "a@b.com"


# ── Password Hashing ─────────────────────────────────────────────────────────


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("MySecurePassword123!")
        assert verify_password("MySecurePassword123!", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("plaintext")
        assert hashed != "plaintext"
        assert "$" in hashed  # bcrypt hashes contain $

    def test_different_hashes_for_same_password(self):
        """Different salts produce different hashes."""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2

    def test_verify_with_corrupt_hash(self):
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


# ── Token Utilities ──────────────────────────────────────────────────────────


class TestTokenUtilities:
    def test_generate_token_length(self):
        token = generate_token(32)
        assert len(token) == 64  # hex encoding doubles length

    def test_generate_token_unique(self):
        t1 = generate_token()
        t2 = generate_token()
        assert t1 != t2

    def test_hash_token_deterministic(self):
        h1 = hash_token("same-token")
        h2 = hash_token("same-token")
        assert h1 == h2

    def test_hash_token_different_inputs(self):
        h1 = hash_token("token-a")
        h2 = hash_token("token-b")
        assert h1 != h2

    def test_verify_token_hash_correct(self):
        token = "my-secret-token"
        h = hash_token(token)
        assert verify_token_hash(token, h) is True

    def test_verify_token_hash_wrong(self):
        h = hash_token("correct-token")
        assert verify_token_hash("wrong-token", h) is False

    def test_generate_token_pair(self):
        token, token_hash = generate_token_pair()
        assert len(token) == 64
        assert verify_token_hash(token, token_hash) is True
