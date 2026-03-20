"""FKWallet Python SDK.

Quick start::

    import asyncio
    from fkwallet import FKWalletClient

    async def main():
        async with FKWalletClient(
            public_key="YOUR_PUBLIC_KEY",
            private_key="YOUR_PRIVATE_KEY",
        ) as client:
            balance = await client.get_balance()
            print(balance.value, balance.currency_code)

    asyncio.run(main())
"""

from .client import FKWalletClient
from .exceptions import FKWalletAPIError, FKWalletError, FKWalletWebhookError
from .models import (
    Balance,
    Currency,
    HistoryItem,
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
from .webhook import compute_webhook_sign, verify_webhook

__all__ = [
    "FKWalletClient",
    "FKWalletError",
    "FKWalletAPIError",
    "FKWalletWebhookError",
    # models
    "Balance",
    "Currency",
    "HistoryItem",
    "MobileCarrier",
    "OnlineProductRequest",
    "OnlineProductResponse",
    "PaymentSystem",
    "Product",
    "ProductCategory",
    "SBPBank",
    "TransferRequest",
    "TransferResponse",
    "TransferStatus",
    "WithdrawalRequest",
    "WithdrawalResponse",
    "WithdrawalStatus",
    "WithdrawalStatusResponse",
    # webhook
    "compute_webhook_sign",
    "verify_webhook",
]

__version__ = "0.1.0"
