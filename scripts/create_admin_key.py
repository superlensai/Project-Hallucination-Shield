"""
Bootstrap script to create the initial admin API key.

Run once after deploying:
    python -m scripts.create_admin_key

The generated key is printed to stdout — store it securely!
"""
import asyncio
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import AsyncSessionLocal
from src.auth.models import APIKey
from src.auth.dependencies import hash_key


async def main():
    raw_key = APIKey.generate_key()
    key_hash_value = hash_key(raw_key)

    api_key = APIKey(
        name="bootstrap-admin",
        key_hash=key_hash_value,
        key_prefix=raw_key[:8],
        scopes=["admin", "read", "write"],
        rate_limit=1000,
    )

    async with AsyncSessionLocal() as session:
        session.add(api_key)
        await session.commit()

    print("=" * 60)
    print("ADMIN API KEY CREATED — STORE THIS SECURELY!")
    print("=" * 60)
    print(f"  Key:    {raw_key}")
    print(f"  Prefix: {raw_key[:8]}")
    print(f"  Scopes: admin, read, write")
    print("=" * 60)
    print("This key will NOT be shown again.")


if __name__ == "__main__":
    asyncio.run(main())
