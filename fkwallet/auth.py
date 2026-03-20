"""SHA-256 signing helpers for FKWallet API authentication."""

import hashlib
import json


def sign_get(private_key: str) -> str:
    """Compute the HMAC-like sign for a GET request (empty body).

    For GET requests the signature is simply ``sha256(private_key)``.

    Args:
        private_key: Your FKWallet private API key.

    Returns:
        Hex-encoded SHA-256 digest.

    Example::

        sign = sign_get("my_private_key")
    """
    return hashlib.sha256(private_key.encode()).hexdigest()


def sign_post(body: dict, private_key: str) -> str:
    """Compute the signature for a POST request.

    Serialises *body* to compact JSON (no spaces), appends ``private_key``,
    then returns ``sha256(json_body + private_key)``.

    Args:
        body: Request payload that will be sent as JSON.
        private_key: Your FKWallet private API key.

    Returns:
        Hex-encoded SHA-256 digest.

    Example::

        sign = sign_post({"amount": 100, "currency_id": 1}, "my_private_key")
    """
    body_str = json.dumps(body, separators=(",", ":"))
    raw = body_str + private_key
    return hashlib.sha256(raw.encode()).hexdigest()
