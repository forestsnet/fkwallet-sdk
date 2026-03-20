"""Pydantic v2 models for FKWallet API responses."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Status enums
# ---------------------------------------------------------------------------


class WithdrawalStatus(IntEnum):
    """Possible states of a withdrawal order."""

    NEW = 0
    DONE = 1
    PROCESSING_2 = 2
    PROCESSING_3 = 3
    PROCESSING_4 = 4
    IN_PROGRESS = 5
    ERROR_8 = 8
    CANCELLED = 9
    ERROR_10 = 10
    PROCESSING_11 = 11

    @property
    def is_processing(self) -> bool:
        """Return True for any processing-type status."""
        return self in (
            self.PROCESSING_2,
            self.PROCESSING_3,
            self.PROCESSING_4,
            self.PROCESSING_11,
            self.IN_PROGRESS,
        )

    @property
    def is_error(self) -> bool:
        """Return True for error statuses."""
        return self in (self.ERROR_8, self.ERROR_10)

    @property
    def is_terminal(self) -> bool:
        """Return True if the order has reached a final state."""
        return self in (self.DONE, self.CANCELLED, self.ERROR_8, self.ERROR_10)


class TransferStatus(IntEnum):
    """Possible states of an inter-wallet transfer."""

    NEW = 0
    DONE = 1
    PROCESSING = 2
    ERROR = 8
    CANCELLED = 9

    @property
    def is_terminal(self) -> bool:
        """Return True if the transfer has reached a final state."""
        return self in (self.DONE, self.CANCELLED, self.ERROR)


# ---------------------------------------------------------------------------
# Common / account models
# ---------------------------------------------------------------------------


class Balance(BaseModel):
    """Wallet balance information."""

    currency_code: str = Field(..., description="ISO currency code, e.g. 'RUB'")
    value: float = Field(..., description="Current balance amount")


class HistoryItem(BaseModel):
    """A single entry in the transaction history.

    The API may return arbitrary additional fields; they are stored in
    ``extra``.
    """

    model_config = {"extra": "allow"}


class Currency(BaseModel):
    """Supported currency entry."""

    id: int
    code: str = Field(..., description="ISO currency code")
    course: float = Field(..., description="Exchange rate")


class PaymentSystem(BaseModel):
    """Supported payment system."""

    id: int
    code: str


class SBPBank(BaseModel):
    """Russian SBP (Faster Payments System) bank entry."""

    id: int
    name: str


class MobileCarrier(BaseModel):
    """Mobile carrier (for mobile top-ups)."""

    id: int
    name: str


# ---------------------------------------------------------------------------
# Withdrawal models
# ---------------------------------------------------------------------------


class WithdrawalRequest(BaseModel):
    """Payload for creating a withdrawal order."""

    amount: float = Field(..., description="Amount to withdraw")
    currency_id: int = Field(..., description="Currency identifier")
    payment_system_id: int = Field(..., description="Payment system identifier")
    fee_from_balance: bool = Field(
        ..., description="If True, the fee is deducted from your balance"
    )
    account: str = Field(..., description="Destination account / wallet number")
    description: str | None = Field(None, description="Optional free-text description")
    order_id: str | None = Field(None, description="Your internal order identifier")
    fields: dict[str, Any] | None = Field(
        None, description="Extra payment-system-specific fields"
    )
    idempotence_key: str = Field(
        ..., description="Unique key to prevent duplicate operations"
    )


class WithdrawalResponse(BaseModel):
    """Response from the withdrawal creation endpoint."""

    id: int
    status: WithdrawalStatus


class WithdrawalStatusResponse(BaseModel):
    """Response from the withdrawal status endpoint."""

    id: int
    status: WithdrawalStatus


# ---------------------------------------------------------------------------
# Transfer models
# ---------------------------------------------------------------------------


class TransferRequest(BaseModel):
    """Payload for creating an inter-wallet transfer."""

    to_wallet_id: int = Field(..., description="Destination wallet identifier")
    amount: float
    currency_id: int
    fee_from_balance: bool
    description: str | None = None
    idempotence_key: str


class TransferResponse(BaseModel):
    """Response from transfer creation or status endpoint."""

    id: int
    from_wallet_number: str
    to_wallet_number: str
    status: TransferStatus


# ---------------------------------------------------------------------------
# Online Products (OP) models
# ---------------------------------------------------------------------------


class ProductCategory(BaseModel):
    """A top-level online-product category.

    May contain additional fields returned by the API.
    """

    model_config = {"extra": "allow"}

    id: int
    name: str | None = None


class Product(BaseModel):
    """An individual online product within a category."""

    model_config = {"extra": "allow"}

    id: int
    name: str | None = None


class OnlineProductRequest(BaseModel):
    """Payload for purchasing an online product."""

    online_product_id: int
    currency_id: int
    amount: float | None = None
    fields: list[dict[str, Any]] = Field(default_factory=list)
    idempotence_key: str


class OnlineProductResponse(BaseModel):
    """Response from online product purchase or status check."""

    id: int
    status: str
    coupon_code: str | None = None
