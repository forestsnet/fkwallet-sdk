"""Example: transfer funds between wallets."""

import asyncio
import uuid

from fkwallet import FKWalletClient, TransferRequest, TransferStatus

PUBLIC_KEY = "YOUR_PUBLIC_KEY"
PRIVATE_KEY = "YOUR_PRIVATE_KEY"


async def main() -> None:
    async with FKWalletClient(public_key=PUBLIC_KEY, private_key=PRIVATE_KEY) as client:
        req = TransferRequest(
            to_wallet_id=12345,
            amount=200.0,
            currency_id=1,
            fee_from_balance=False,
            description="Payment for services",
            idempotence_key=str(uuid.uuid4()),
        )

        transfer = await client.create_transfer(req)
        print(
            f"Transfer created: id={transfer.id}\n"
            f"  From: {transfer.from_wallet_number}\n"
            f"  To:   {transfer.to_wallet_number}\n"
            f"  Status: {transfer.status.name}"
        )

        # Poll until complete
        while not transfer.status.is_terminal:
            await asyncio.sleep(3)
            transfer = await client.get_transfer(transfer.id)
            print(f"  → status: {transfer.status.name}")

        if transfer.status == TransferStatus.DONE:
            print("✅ Transfer completed!")
        elif transfer.status == TransferStatus.CANCELLED:
            print("⚠️  Transfer cancelled.")
        else:
            print("❌ Transfer failed.")


if __name__ == "__main__":
    asyncio.run(main())
