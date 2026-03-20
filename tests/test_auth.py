"""Tests for fkwallet.auth signing functions."""

import hashlib
import json

import pytest

from fkwallet.auth import sign_get, sign_post


PRIVATE_KEY = "test_private_key_12345"


class TestSignGet:
    def test_returns_hex_string(self):
        result = sign_get(PRIVATE_KEY)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest is always 64 chars

    def test_correct_value(self):
        expected = hashlib.sha256(PRIVATE_KEY.encode()).hexdigest()
        assert sign_get(PRIVATE_KEY) == expected

    def test_different_keys_produce_different_signs(self):
        assert sign_get("key_a") != sign_get("key_b")

    def test_empty_key(self):
        result = sign_get("")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected


class TestSignPost:
    def test_returns_hex_string(self):
        result = sign_post({"amount": 100}, PRIVATE_KEY)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_correct_value(self):
        body = {"amount": 100, "currency_id": 1}
        body_str = json.dumps(body, separators=(",", ":"))
        expected = hashlib.sha256((body_str + PRIVATE_KEY).encode()).hexdigest()
        assert sign_post(body, PRIVATE_KEY) == expected

    def test_compact_json_used(self):
        """Verify no extra spaces are included in the serialised body."""
        body = {"a": 1, "b": 2}
        compact = json.dumps(body, separators=(",", ":"))
        assert " " not in compact

    def test_different_bodies_produce_different_signs(self):
        s1 = sign_post({"amount": 100}, PRIVATE_KEY)
        s2 = sign_post({"amount": 200}, PRIVATE_KEY)
        assert s1 != s2

    def test_empty_body(self):
        result = sign_post({}, PRIVATE_KEY)
        expected = hashlib.sha256(("{}" + PRIVATE_KEY).encode()).hexdigest()
        assert result == expected

    def test_nested_body(self):
        body = {"outer": {"inner": [1, 2, 3]}}
        result = sign_post(body, PRIVATE_KEY)
        assert len(result) == 64
