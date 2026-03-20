"""Async FKWallet API client."""

from __future__ import annotations

import json
from typing import Any

import httpx

from .auth import sign_get, sign_post
from .exceptions import FKWalletAPIError
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
    WithdrawalRequest,
    WithdrawalResponse,
    WithdrawalStatusResponse,
)

BASE_URL = "https://api.fkwallet.io/v1"


class FKWalletClient:
    """Asynchronous client for the FKWallet API.

    Use as an async context manager to automatically manage the underlying
    HTTP connection pool::

        async with FKWalletClient(public_key="...", private_key="...") as client:
            balance = await client.get_balance()

    Args:
        public_key: Your FKWallet public key.
        private_key: Your FKWallet private key (used for signing).
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds (default: 30).
    """

    def __init__(
        self,
        public_key: str,
        private_key: str,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._public_key = public_key
        self._private_key = private_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Context-manager helpers
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "FKWalletClient":
        await self.open()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def open(self) -> None:
        """Open the underlying HTTP client session."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Build a full URL for the given *path* under the public-key prefix."""
        return f"{self._base_url}/{self._public_key}/{path.lstrip('/')}"

    def _get_headers(self, sign: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {sign}",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Execute an authenticated GET request and return the inner data payload."""
        if self._client is None:
            raise RuntimeError(
                "Client is not open. Use 'async with FKWalletClient(...) as client'"
            )
        sign = sign_get(self._private_key)
        response = await self._client.get(
            self._url(path),
            params={k: v for k, v in (params or {}).items() if v is not None},
            headers=self._get_headers(sign),
        )
        return self._parse(response)

    async def _post(self, path: str, body: dict[str, Any]) -> Any:
        """Execute an authenticated POST request and return the inner data payload."""
        if self._client is None:
            raise RuntimeError(
                "Client is not open. Use 'async with FKWalletClient(...) as client'"
            )
        sign = sign_post(body, self._private_key)
        response = await self._client.post(
            self._url(path),
            content=json.dumps(body, separators=(",", ":")),
            headers=self._get_headers(sign),
        )
        return self._parse(response)

    @staticmethod
    def _parse(response: httpx.Response) -> Any:
        """Parse the API response envelope and raise on errors.

        Expected envelope::

            {"data": {"status": "ok", "data": <payload>}}

        Raises:
            FKWalletAPIError: On HTTP errors or when ``status != "ok"``.
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise FKWalletAPIError(
                f"HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
            ) from exc

        try:
            wrapper = response.json()
        except Exception as exc:
            raise FKWalletAPIError(
                f"Invalid JSON response: {response.text}"
            ) from exc

        outer = wrapper.get("data", {})

        # Some endpoints return {"data": [...]} directly (list payload),
        # others return {"data": {"status": "ok", "data": <payload>}}
        if isinstance(outer, list):
            return outer

        status = outer.get("status")
        if status != "ok":
            raise FKWalletAPIError(
                f"API error: status={status!r}",
                status_code=response.status_code,
                raw=outer,
            )

        inner = outer.get("data")
        # If inner is also a list, return it directly
        if isinstance(inner, list):
            return inner

        return inner

    # ------------------------------------------------------------------
    # Account / misc endpoints
    # ------------------------------------------------------------------

    async def get_balance(self) -> Balance:
        """Fetch the current wallet balance.

        Returns:
            :class:`~fkwallet.models.Balance` with ``currency_code`` and
            ``value``.

        Raises:
            FKWalletAPIError: On API or HTTP error.
        """
        data = await self._get("balance")
        return Balance.model_validate(data)

    async def get_history(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> list[HistoryItem]:
        """Fetch transaction history.

        Args:
            date_from: Start date filter (``YYYY-MM-DD``).
            date_to: End date filter (``YYYY-MM-DD``).
            page: Page number (1-indexed).
            limit: Number of records per page.

        Returns:
            List of :class:`~fkwallet.models.HistoryItem` entries.
        """
        data = await self._get(
            "history",
            params={
                "date_from": date_from,
                "date_to": date_to,
                "page": page,
                "limit": limit,
            },
        )
        return [HistoryItem.model_validate(item) for item in (data or [])]

    async def get_currencies(self) -> list[Currency]:
        """List all supported currencies.

        Returns:
            List of :class:`~fkwallet.models.Currency` objects.
        """
        data = await self._get("currencies")
        return [Currency.model_validate(c) for c in (data or [])]

    async def get_payment_systems(self) -> list[PaymentSystem]:
        """List all supported payment systems.

        Returns:
            List of :class:`~fkwallet.models.PaymentSystem` objects.
        """
        data = await self._get("payment_systems")
        return [PaymentSystem.model_validate(p) for p in (data or [])]

    async def get_sbp_list(self) -> list[SBPBank]:
        """List banks available via the Russian SBP (Faster Payments System).

        Returns:
            List of :class:`~fkwallet.models.SBPBank` objects.
        """
        data = await self._get("sbp_list")
        return [SBPBank.model_validate(b) for b in (data or [])]

    async def get_mobile_carrier_list(self) -> list[MobileCarrier]:
        """List mobile carriers available for top-up.

        Returns:
            List of :class:`~fkwallet.models.MobileCarrier` objects.
        """
        data = await self._get("mobile_carrier_list")
        return [MobileCarrier.model_validate(c) for c in (data or [])]

    # ------------------------------------------------------------------
    # Withdrawal endpoints
    # ------------------------------------------------------------------

    async def create_withdrawal(self, request: WithdrawalRequest) -> WithdrawalResponse:
        """Create a new withdrawal order.

        Args:
            request: Withdrawal parameters.

        Returns:
            :class:`~fkwallet.models.WithdrawalResponse` with ``id`` and
            ``status``.

        Raises:
            FKWalletAPIError: On API or HTTP error.
        """
        body = request.model_dump(exclude_none=True)
        data = await self._post("withdrawal", body)
        return WithdrawalResponse.model_validate(data)

    async def get_withdrawal_status(
        self, order_id: str, lookup_type: str = "id"
    ) -> WithdrawalStatusResponse:
        """Get the status of an existing withdrawal order.

        Args:
            order_id: The withdrawal identifier.
            lookup_type: Either ``"id"`` (default) or ``"order_id"`` to look
                up by your internal order identifier.

        Returns:
            :class:`~fkwallet.models.WithdrawalStatusResponse`.
        """
        data = await self._get(
            f"withdrawal/{order_id}", params={"type": lookup_type}
        )
        return WithdrawalStatusResponse.model_validate(data)

    # ------------------------------------------------------------------
    # Transfer endpoints
    # ------------------------------------------------------------------

    async def create_transfer(self, request: TransferRequest) -> TransferResponse:
        """Create a new inter-wallet transfer.

        Args:
            request: Transfer parameters.

        Returns:
            :class:`~fkwallet.models.TransferResponse`.

        Raises:
            FKWalletAPIError: On API or HTTP error.
        """
        body = request.model_dump(exclude_none=True)
        data = await self._post("transfer", body)
        return TransferResponse.model_validate(data)

    async def get_transfer(self, transfer_id: int) -> TransferResponse:
        """Get the status/details of an existing transfer.

        Args:
            transfer_id: Transfer identifier returned by
                :meth:`create_transfer`.

        Returns:
            :class:`~fkwallet.models.TransferResponse`.
        """
        data = await self._get(f"transfer/{transfer_id}")
        return TransferResponse.model_validate(data)

    # ------------------------------------------------------------------
    # Online Products endpoints
    # ------------------------------------------------------------------

    async def get_op_categories(self) -> list[ProductCategory]:
        """List all online-product categories.

        Returns:
            List of :class:`~fkwallet.models.ProductCategory` objects.
        """
        data = await self._get("op/categories")
        return [ProductCategory.model_validate(c) for c in (data or [])]

    async def get_op_products(self, category_id: int) -> list[Product]:
        """List products within a category.

        Args:
            category_id: Category identifier from :meth:`get_op_categories`.

        Returns:
            List of :class:`~fkwallet.models.Product` objects.
        """
        data = await self._get(f"op/categories/{category_id}/products")
        return [Product.model_validate(p) for p in (data or [])]

    async def create_op_order(
        self, request: OnlineProductRequest
    ) -> OnlineProductResponse:
        """Purchase an online product.

        Args:
            request: Order parameters including ``online_product_id``,
                ``currency_id``, optional ``amount``, ``fields``, and
                ``idempotence_key``.

        Returns:
            :class:`~fkwallet.models.OnlineProductResponse` with ``id``,
            ``status``, and optional ``coupon_code``.
        """
        body = request.model_dump(exclude_none=True)
        data = await self._post("op/create", body)
        return OnlineProductResponse.model_validate(data)

    async def get_op_status(self, order_id: int) -> OnlineProductResponse:
        """Get the status of an online-product order.

        Args:
            order_id: Order identifier returned by :meth:`create_op_order`.

        Returns:
            :class:`~fkwallet.models.OnlineProductResponse`.
        """
        data = await self._get(f"op/status/{order_id}")
        return OnlineProductResponse.model_validate(data)
