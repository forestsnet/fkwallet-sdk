"""Tests for fkwallet.webhook verification."""

import hashlib

import pytest

from fkwallet.exceptions import FKWalletWebhookError
from fkwallet.webhook import compute_webhook_sign, verify_webhook

PRIVATE_KEY = "webhook_secret_key"


def _build_sign(form_data: dict, private_key: str) -> str:
    filtered = {k: v for k, v in form_data.items() if k != "sign"}
    sorted_values = [v for _, v in sorted(filtered.items())]
    joined = "|".join(sorted_values) + private_key
    return hashlib.sha256(joined.encode()).hexdigest()


class TestComputeWebhookSign:
    def test_basic(self):
        data = {"order_id": "123", "amount": "500", "currency": "RUB"}
        result = compute_webhook_sign(data, PRIVATE_KEY)
        assert len(result) == 64
        assert result == _build_sign(data, PRIVATE_KEY)

    def test_sign_field_excluded(self):
        data = {"order_id": "123", "sign": "should_be_ignored"}
        r1 = compute_webhook_sign(data, PRIVATE_KEY)
        data2 = {"order_id": "123"}
        r2 = compute_webhook_sign(data2, PRIVATE_KEY)
        assert r1 == r2

    def test_sorted_by_key(self):
        data_unsorted = {"z_field": "last", "a_field": "first"}
        data_sorted = {"a_field": "first", "z_field": "last"}
        assert compute_webhook_sign(data_unsorted, PRIVATE_KEY) == compute_webhook_sign(
            data_sorted, PRIVATE_KEY
        )

    def test_empty_data(self):
        result = compute_webhook_sign({}, PRIVATE_KEY)
        expected = hashlib.sha256(PRIVATE_KEY.encode()).hexdigest()
        assert result == expected


class TestVerifyWebhook:
    def _make_payload(self, extra: dict | None = None) -> dict:
        base = {"order_id": "42", "amount": "100", "currency": "RUB"}
        if extra:
            base.update(extra)
        sign = _build_sign(base, PRIVATE_KEY)
        base["sign"] = sign
        return base

    def test_valid_signature(self):
        payload = self._make_payload()
        assert verify_webhook(payload, PRIVATE_KEY) is True

    def test_missing_sign_raises(self):
        payload = {"order_id": "42", "amount": "100"}
        with pytest.raises(FKWalletWebhookError, match="missing 'sign' field"):
            verify_webhook(payload, PRIVATE_KEY)

    def test_wrong_sign_raises(self):
        payload = self._make_payload()
        payload["sign"] = "wrong_signature_value" + "0" * 42
        with pytest.raises(FKWalletWebhookError, match="mismatch"):
            verify_webhook(payload, PRIVATE_KEY)

    def test_tampered_value_raises(self):
        payload = self._make_payload()
        payload["amount"] = "99999"  # tamper with amount
        with pytest.raises(FKWalletWebhookError):
            verify_webhook(payload, PRIVATE_KEY)

    def test_wrong_private_key_raises(self):
        payload = self._make_payload()
        with pytest.raises(FKWalletWebhookError):
            verify_webhook(payload, "wrong_private_key")
