"""Tests for FKWalletClient using respx to mock httpx."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from fkwallet.client import FKWalletClient
from fkwallet.exceptions import FKWalletAPIError
from fkwallet.models import (
    Balance,
    Currency,
    MobileCarrier,
    OnlineProductRequest,
    OnlineProductResponse,
    PaymentSystem,
    SBPBank,
    TransferRequest,
    TransferResponse,
    TransferStatus,
    WithdrawalRequest,
    WithdrawalResponse,
    WithdrawalStatus,
    WithdrawalStatusResponse,
)

PUBLIC_KEY = "pub_test"
PRIVATE_KEY = "priv_test"
BASE = f"https://api.fkwallet.io/v1/{PUBLIC_KEY}"


def ok(data) -> dict:
    """Wrap data in the FKWallet envelope."""
    return {"data": {"status": "ok", "data": data}}


def err(msg: str = "error") -> dict:
    return {"data": {"status": "error", "message": msg}}


@pytest.fixture
def client():
    return FKWalletClient(public_key=PUBLIC_KEY, private_key=PRIVATE_KEY)


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_manager():
    async with FKWalletClient(PUBLIC_KEY, PRIVATE_KEY) as c:
        assert c._client is not None
    assert c._client is None


# ---------------------------------------------------------------------------
# get_balance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_balance(client):
    respx.get(f"{BASE}/balance").mock(
        return_value=httpx.Response(200, json=ok({"currency_code": "RUB", "value": 1500.0}))
    )
    async with client:
        balance = await client.get_balance()
    assert isinstance(balance, Balance)
    assert balance.currency_code == "RUB"
    assert balance.value == 1500.0


@pytest.mark.asyncio
@respx.mock
async def test_get_balance_api_error(client):
    respx.get(f"{BASE}/balance").mock(
        return_value=httpx.Response(200, json=err("insufficient funds"))
    )
    async with client:
        with pytest.raises(FKWalletAPIError):
            await client.get_balance()


@pytest.mark.asyncio
@respx.mock
async def test_get_balance_http_error(client):
    respx.get(f"{BASE}/balance").mock(return_value=httpx.Response(401))
    async with client:
        with pytest.raises(FKWalletAPIError) as exc_info:
            await client.get_balance()
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_currencies
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_currencies(client):
    payload = [{"id": 1, "code": "RUB", "course": 1.0}, {"id": 2, "code": "USD", "course": 90.5}]
    respx.get(f"{BASE}/currencies").mock(
        return_value=httpx.Response(200, json=ok(payload))
    )
    async with client:
        currencies = await client.get_currencies()
    assert len(currencies) == 2
    assert isinstance(currencies[0], Currency)
    assert currencies[1].code == "USD"


# ---------------------------------------------------------------------------
# get_payment_systems
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_payment_systems(client):
    respx.get(f"{BASE}/payment_systems").mock(
        return_value=httpx.Response(200, json=ok([{"id": 1, "code": "QIWI"}]))
    )
    async with client:
        ps = await client.get_payment_systems()
    assert len(ps) == 1
    assert isinstance(ps[0], PaymentSystem)


# ---------------------------------------------------------------------------
# get_sbp_list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_sbp_list(client):
    respx.get(f"{BASE}/sbp_list").mock(
        return_value=httpx.Response(200, json=ok([{"id": 1, "name": "Сбербанк"}]))
    )
    async with client:
        banks = await client.get_sbp_list()
    assert isinstance(banks[0], SBPBank)
    assert banks[0].name == "Сбербанк"


# ---------------------------------------------------------------------------
# get_mobile_carrier_list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_mobile_carrier_list(client):
    respx.get(f"{BASE}/mobile_carrier_list").mock(
        return_value=httpx.Response(200, json=ok([{"id": 1, "name": "МТС"}]))
    )
    async with client:
        carriers = await client.get_mobile_carrier_list()
    assert isinstance(carriers[0], MobileCarrier)


# ---------------------------------------------------------------------------
# get_history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_history(client):
    respx.get(f"{BASE}/history").mock(
        return_value=httpx.Response(200, json=ok([{"id": 1, "type": "withdrawal"}]))
    )
    async with client:
        history = await client.get_history(date_from="2024-01-01", limit=10)
    assert len(history) == 1


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_create_withdrawal(client):
    respx.post(f"{BASE}/withdrawal").mock(
        return_value=httpx.Response(200, json=ok({"id": 100, "status": 0}))
    )
    req = WithdrawalRequest(
        amount=500.0,
        currency_id=1,
        payment_system_id=2,
        fee_from_balance=True,
        account="79001234567",
        idempotence_key="idem-1",
    )
    async with client:
        resp = await client.create_withdrawal(req)
    assert isinstance(resp, WithdrawalResponse)
    assert resp.id == 100
    assert resp.status == WithdrawalStatus.NEW


@pytest.mark.asyncio
@respx.mock
async def test_get_withdrawal_status(client):
    respx.get(f"{BASE}/withdrawal/100").mock(
        return_value=httpx.Response(200, json=ok({"id": 100, "status": 1}))
    )
    async with client:
        resp = await client.get_withdrawal_status("100")
    assert isinstance(resp, WithdrawalStatusResponse)
    assert resp.status == WithdrawalStatus.DONE


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_create_transfer(client):
    respx.post(f"{BASE}/transfer").mock(
        return_value=httpx.Response(
            200,
            json=ok(
                {
                    "id": 55,
                    "from_wallet_number": "W100",
                    "to_wallet_number": "W200",
                    "status": 1,
                }
            ),
        )
    )
    req = TransferRequest(
        to_wallet_id=999,
        amount=200.0,
        currency_id=1,
        fee_from_balance=False,
        idempotence_key="transfer-idem",
    )
    async with client:
        resp = await client.create_transfer(req)
    assert isinstance(resp, TransferResponse)
    assert resp.status == TransferStatus.DONE
    assert resp.from_wallet_number == "W100"


@pytest.mark.asyncio
@respx.mock
async def test_get_transfer(client):
    respx.get(f"{BASE}/transfer/55").mock(
        return_value=httpx.Response(
            200,
            json=ok(
                {
                    "id": 55,
                    "from_wallet_number": "W100",
                    "to_wallet_number": "W200",
                    "status": 2,
                }
            ),
        )
    )
    async with client:
        resp = await client.get_transfer(55)
    assert resp.status == TransferStatus.PROCESSING


# ---------------------------------------------------------------------------
# Online Products
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_op_categories(client):
    respx.get(f"{BASE}/op/categories").mock(
        return_value=httpx.Response(
            200, json=ok([{"id": 1, "name": "Games"}, {"id": 2, "name": "Software"}])
        )
    )
    async with client:
        cats = await client.get_op_categories()
    assert len(cats) == 2
    assert cats[0].name == "Games"


@pytest.mark.asyncio
@respx.mock
async def test_get_op_products(client):
    respx.get(f"{BASE}/op/categories/1/products").mock(
        return_value=httpx.Response(
            200, json=ok([{"id": 10, "name": "Steam $10"}])
        )
    )
    async with client:
        products = await client.get_op_products(1)
    assert products[0].name == "Steam $10"


@pytest.mark.asyncio
@respx.mock
async def test_create_op_order(client):
    respx.post(f"{BASE}/op/create").mock(
        return_value=httpx.Response(
            200, json=ok({"id": 77, "status": "done", "coupon_code": "GIFT123"})
        )
    )
    req = OnlineProductRequest(
        online_product_id=10,
        currency_id=1,
        fields=[],
        idempotence_key="op-idem",
    )
    async with client:
        resp = await client.create_op_order(req)
    assert isinstance(resp, OnlineProductResponse)
    assert resp.coupon_code == "GIFT123"


@pytest.mark.asyncio
@respx.mock
async def test_get_op_status(client):
    respx.get(f"{BASE}/op/status/77").mock(
        return_value=httpx.Response(
            200, json=ok({"id": 77, "status": "processing"})
        )
    )
    async with client:
        resp = await client.get_op_status(77)
    assert resp.status == "processing"
    assert resp.coupon_code is None


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_client_not_open_raises():
    c = FKWalletClient(PUBLIC_KEY, PRIVATE_KEY)
    with pytest.raises(RuntimeError, match="not open"):
        await c.get_balance()


@pytest.mark.asyncio
@respx.mock
async def test_invalid_json_raises(client):
    respx.get(f"{BASE}/balance").mock(
        return_value=httpx.Response(200, content=b"not-json")
    )
    async with client:
        with pytest.raises(FKWalletAPIError, match="Invalid JSON"):
            await client.get_balance()
