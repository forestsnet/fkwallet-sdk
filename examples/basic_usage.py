"""Basic FKWallet SDK usage: balance, currencies, payment systems."""

import asyncio

from fkwallet import FKWalletClient

PUBLIC_KEY = "YOUR_PUBLIC_KEY"
PRIVATE_KEY = "YOUR_PRIVATE_KEY"


async def main() -> None:
    async with FKWalletClient(public_key=PUBLIC_KEY, private_key=PRIVATE_KEY) as client:
        # --- Balance ---
        balance = await client.get_balance()
        print(f"Balance: {balance.value} {balance.currency_code}")

        # --- Currencies ---
        currencies = await client.get_currencies()
        print("\nSupported currencies:")
        for c in currencies:
            print(f"  [{c.id}] {c.code}  (rate: {c.course})")

        # --- Payment systems ---
        payment_systems = await client.get_payment_systems()
        print("\nPayment systems:")
        for ps in payment_systems:
            print(f"  [{ps.id}] {ps.code}")

        # --- SBP banks ---
        sbp = await client.get_sbp_list()
        print(f"\nSBP banks available: {len(sbp)}")

        # --- Mobile carriers ---
        carriers = await client.get_mobile_carrier_list()
        print(f"Mobile carriers available: {len(carriers)}")

        # --- Transaction history ---
        history = await client.get_history(page=1, limit=5)
        print(f"\nLast {len(history)} transactions fetched")


if __name__ == "__main__":
    asyncio.run(main())
