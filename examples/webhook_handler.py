"""Example: FastAPI webhook handler with FKWallet signature verification.

Install FastAPI + uvicorn to run:
    pip install fastapi uvicorn
    uvicorn webhook_handler:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, Form, HTTPException, Request

from fkwallet.exceptions import FKWalletWebhookError
from fkwallet.webhook import verify_webhook

app = FastAPI(title="FKWallet Webhook Handler")

PRIVATE_KEY = "YOUR_PRIVATE_KEY"  # load from env in production


@app.post("/webhook/fkwallet")
async def fkwallet_webhook(request: Request):
    """Receive and verify an FKWallet webhook notification.

    FKWallet sends a POST request with form-data fields.
    The ``sign`` field contains the HMAC used to verify authenticity.
    """
    form_data = dict(await request.form())

    try:
        verify_webhook(form_data, private_key=PRIVATE_KEY)
    except FKWalletWebhookError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # All good — process the notification
    order_id = form_data.get("order_id")
    status = form_data.get("status")

    print(f"[Webhook] order_id={order_id!r}  status={status!r}")
    print(f"[Webhook] full payload: {form_data}")

    # Here you would update your database, notify users, etc.
    return {"ok": True}
