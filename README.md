# fkwallet-sdk

Async Python SDK for the [FKWallet](https://fkwallet.io) API.

## Features

- ✅ Fully async (`httpx` + `async/await`)
- ✅ Pydantic v2 models with full type hints
- ✅ SHA-256 request signing (GET & POST)
- ✅ Webhook signature verification
- ✅ Custom exceptions
- ✅ Typed status enums with helper properties

## Installation

```bash
pip install fkwallet-sdk
```

Or with Poetry:

```bash
poetry add fkwallet-sdk
```

## Quick Start

```python
import asyncio
from fkwallet import FKWalletClient

async def main():
    async with FKWalletClient(
        public_key="YOUR_PUBLIC_KEY",
        private_key="YOUR_PRIVATE_KEY",
    ) as client:
        balance = await client.get_balance()
        print(f"Balance: {balance.value} {balance.currency_code}")

asyncio.run(main())
```

## API Reference

### `FKWalletClient`

All methods are `async` and must be used inside an `async with` block.

| Method | Description |
|---|---|
| `get_balance()` | Current wallet balance |
| `get_history(date_from, date_to, page, limit)` | Transaction history |
| `get_currencies()` | List supported currencies |
| `get_payment_systems()` | List payment systems |
| `get_sbp_list()` | List SBP banks |
| `get_mobile_carrier_list()` | List mobile carriers |
| `create_withdrawal(request)` | Create withdrawal order |
| `get_withdrawal_status(order_id, type)` | Get withdrawal status |
| `create_transfer(request)` | Transfer to another wallet |
| `get_transfer(id)` | Get transfer status |
| `get_op_categories()` | Online product categories |
| `get_op_products(category_id)` | Products in a category |
| `create_op_order(request)` | Purchase online product |
| `get_op_status(order_id)` | Online product order status |

### Webhook Verification

```python
from fkwallet.webhook import verify_webhook

# In your web framework:
form_data = dict(await request.form())
verify_webhook(form_data, private_key="YOUR_PRIVATE_KEY")
# Raises FKWalletWebhookError on invalid signature
```

### Status Enums

```python
from fkwallet import WithdrawalStatus

status = WithdrawalStatus(2)
status.is_processing  # True
status.is_terminal    # False
status.is_error       # False
```

## Error Handling

```python
from fkwallet import FKWalletAPIError

try:
    result = await client.create_withdrawal(...)
except FKWalletAPIError as e:
    print(e.message, e.status_code, e.raw)
```

## Development

```bash
poetry install
poetry run pytest tests/ -v
```

## License

MIT
