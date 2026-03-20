"""Custom exceptions for FKWallet SDK."""


class FKWalletError(Exception):
    """Base exception for FKWallet SDK."""


class FKWalletAPIError(FKWalletError):
    """Raised when the API returns a non-ok status or HTTP error.

    Attributes:
        status_code: HTTP status code (if applicable).
        message: Error message from the API.
        raw: Raw response data (if available).
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        raw: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.raw = raw or {}

    def __repr__(self) -> str:
        return (
            f"FKWalletAPIError(message={self.message!r},"
            f" status_code={self.status_code!r})"
        )


class FKWalletWebhookError(FKWalletError):
    """Raised when webhook signature verification fails."""
