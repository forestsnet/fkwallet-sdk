"""Webhook signature verification for FKWallet callbacks."""

import hashlib

from .exceptions import FKWalletWebhookError


def compute_webhook_sign(form_data: dict[str, str], private_key: str) -> str:
    """Compute the expected webhook signature.

    The algorithm is:
    1. Sort form-data fields by key (ascending).
    2. Join their *values* with ``|``.
    3. Append ``private_key`` to the joined string.
    4. Return ``sha256(joined + private_key)`` as a hex digest.

    The ``sign`` field itself is **excluded** from the computation because it
    is the expected output, not an input.

    Args:
        form_data: Raw POST form-data as a ``{key: value}`` mapping.
            The ``sign`` field is automatically excluded.
        private_key: Your FKWallet private API key.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    filtered = {k: v for k, v in form_data.items() if k != "sign"}
    sorted_values = [v for _, v in sorted(filtered.items())]
    joined = "|".join(sorted_values) + private_key
    return hashlib.sha256(joined.encode()).hexdigest()


def verify_webhook(form_data: dict[str, str], private_key: str) -> bool:
    """Verify an incoming FKWallet webhook signature.

    Args:
        form_data: Complete POST form-data including the ``sign`` field.
        private_key: Your FKWallet private API key.

    Returns:
        ``True`` if the signature is valid.

    Raises:
        FKWalletWebhookError: If the ``sign`` field is missing or the
            signature does not match.

    Example::

        from fkwallet.webhook import verify_webhook

        @app.post("/webhook")
        async def handle(request: Request):
            data = dict(await request.form())
            verify_webhook(data, private_key=settings.FK_PRIVATE_KEY)
            # process ...
    """
    incoming_sign = form_data.get("sign")
    if not incoming_sign:
        raise FKWalletWebhookError("Webhook payload missing 'sign' field")

    expected = compute_webhook_sign(form_data, private_key)
    if not _secure_compare(incoming_sign, expected):
        raise FKWalletWebhookError(
            "Webhook signature mismatch: possible tampering detected"
        )
    return True


def _secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0
