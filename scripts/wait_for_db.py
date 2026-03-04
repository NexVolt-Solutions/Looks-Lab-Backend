import asyncio
import os
import sys

import asyncpg


async def wait_for_db(max_retries: int = 30, delay: int = 2) -> None:
    db_uri = os.getenv("DATABASE_URI", "").replace("postgresql+asyncpg://", "postgresql://")

    print("Waiting for database...")

    for attempt in range(max_retries):
        try:
            conn = await asyncpg.connect(db_uri)
            await conn.close()
            print("Database is ready")
            return
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(delay)

    print("Database unavailable after maximum retries")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(wait_for_db())

