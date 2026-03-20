"""Example: create a withdrawal and poll until it reaches a terminal state."""

import asyncio
import uuid

from fkwallet import FKWalletClient, WithdrawalRequest, WithdrawalStatus

PUBLIC_KEY = "YOUR_PUBLIC_KEY"
PRIVATE_KEY = "YOUR_PRIVATE_KEY"


async def main() -> None:
    async with FKWalletClient(public_key=PUBLIC_KEY, private_key=PRIVATE_KEY) as client:
        # Create a new withdrawal
        req = WithdrawalRequest(
            amount=500.0,
            currency_id=1,          # RUB
            payment_system_id=5,    # e.g. SBP
            fee_from_balance=True,
            account="79001234567",
            description="Test withdrawal",
            idempotence_key=str(uuid.uuid4()),
        )

        result = await client.create_withdrawal(req)
        print(f"Withdrawal created: id={result.id}, status={result.status.name}")

        # Poll until terminal
        while not result.status.is_terminal:
            await asyncio.sleep(5)
            status_resp = await client.get_withdrawal_status(str(result.id))
            result.status = status_resp.status
            print(f"  → status: {result.status.name}")

        if result.status == WithdrawalStatus.DONE:
            print("✅ Withdrawal completed successfully!")
        elif result.status.is_error:
            print("❌ Withdrawal failed.")
        else:
            print(f"⚠️  Withdrawal ended with status: {result.status.name}")


if __name__ == "__main__":
    asyncio.run(main())
