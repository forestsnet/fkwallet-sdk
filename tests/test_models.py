"""Tests for fkwallet.models Pydantic models."""

import pytest
from pydantic import ValidationError

from fkwallet.models import (
    Balance,
    Currency,
    MobileCarrier,
    OnlineProductRequest,
    OnlineProductResponse,
    PaymentSystem,
    Product,
    ProductCategory,
    SBPBank,
    TransferRequest,
    TransferResponse,
    TransferStatus,
    WithdrawalRequest,
    WithdrawalResponse,
    WithdrawalStatus,
    WithdrawalStatusResponse,
)


class TestBalance:
    def test_valid(self):
        b = Balance(currency_code="RUB", value=1000.50)
        assert b.currency_code == "RUB"
        assert b.value == 1000.50

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            Balance(currency_code="RUB")  # missing value


class TestCurrency:
    def test_valid(self):
        c = Currency(id=1, code="RUB", course=1.0)
        assert c.id == 1

    def test_from_dict(self):
        c = Currency.model_validate({"id": 2, "code": "USD", "course": 90.5})
        assert c.code == "USD"


class TestWithdrawalStatus:
    def test_done(self):
        assert WithdrawalStatus(1) == WithdrawalStatus.DONE

    def test_is_processing(self):
        for code in (2, 3, 4, 11, 5):
            s = WithdrawalStatus(code)
            assert s.is_processing

    def test_is_error(self):
        assert WithdrawalStatus.ERROR_8.is_error
        assert WithdrawalStatus.ERROR_10.is_error

    def test_is_terminal(self):
        assert WithdrawalStatus.DONE.is_terminal
        assert WithdrawalStatus.CANCELLED.is_terminal
        assert not WithdrawalStatus.NEW.is_terminal

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            WithdrawalStatus(99)


class TestTransferStatus:
    def test_done_is_terminal(self):
        assert TransferStatus.DONE.is_terminal

    def test_processing_not_terminal(self):
        assert not TransferStatus.PROCESSING.is_terminal


class TestWithdrawalRequest:
    def test_valid(self):
        req = WithdrawalRequest(
            amount=500.0,
            currency_id=1,
            payment_system_id=2,
            fee_from_balance=True,
            account="79001234567",
            idempotence_key="unique-key-1",
        )
        assert req.account == "79001234567"
        assert req.description is None

    def test_optional_fields(self):
        req = WithdrawalRequest(
            amount=500.0,
            currency_id=1,
            payment_system_id=2,
            fee_from_balance=False,
            account="acc",
            description="Test desc",
            order_id="my-order-123",
            idempotence_key="key",
        )
        assert req.description == "Test desc"
        assert req.order_id == "my-order-123"


class TestWithdrawalResponse:
    def test_valid(self):
        r = WithdrawalResponse(id=42, status=0)
        assert r.status == WithdrawalStatus.NEW

    def test_status_coercion(self):
        r = WithdrawalResponse.model_validate({"id": 1, "status": 1})
        assert r.status == WithdrawalStatus.DONE


class TestTransferRequest:
    def test_valid(self):
        req = TransferRequest(
            to_wallet_id=99,
            amount=100.0,
            currency_id=1,
            fee_from_balance=True,
            idempotence_key="idem-1",
        )
        assert req.to_wallet_id == 99


class TestTransferResponse:
    def test_valid(self):
        r = TransferResponse.model_validate(
            {
                "id": 10,
                "from_wallet_number": "W001",
                "to_wallet_number": "W002",
                "status": 1,
            }
        )
        assert r.status == TransferStatus.DONE


class TestOnlineProductRequest:
    def test_defaults(self):
        req = OnlineProductRequest(
            online_product_id=5,
            currency_id=1,
            fields=[],
            idempotence_key="key",
        )
        assert req.amount is None
        assert req.fields == []


class TestOnlineProductResponse:
    def test_with_coupon(self):
        r = OnlineProductResponse.model_validate(
            {"id": 1, "status": "done", "coupon_code": "PROMO123"}
        )
        assert r.coupon_code == "PROMO123"

    def test_without_coupon(self):
        r = OnlineProductResponse.model_validate({"id": 2, "status": "processing"})
        assert r.coupon_code is None


class TestPaymentSystem:
    def test_valid(self):
        ps = PaymentSystem(id=1, code="QIWI")
        assert ps.code == "QIWI"


class TestSBPBank:
    def test_valid(self):
        b = SBPBank(id=1, name="Sberbank")
        assert b.name == "Sberbank"


class TestMobileCarrier:
    def test_valid(self):
        mc = MobileCarrier(id=1, name="МТС")
        assert mc.name == "МТС"


class TestProductCategory:
    def test_extra_fields_allowed(self):
        cat = ProductCategory.model_validate({"id": 1, "name": "Games", "icon": "🎮"})
        assert cat.id == 1

    def test_no_name(self):
        cat = ProductCategory.model_validate({"id": 2})
        assert cat.name is None


class TestProduct:
    def test_extra_allowed(self):
        p = Product.model_validate({"id": 10, "name": "Steam Card", "price": 100})
        assert p.id == 10
