import asyncio
import os
import sys
import asyncpg


async def wait_for_db(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready using asyncpg."""
    db_uri = os.getenv('DATABASE_URI', '')

    # asyncpg expects postgresql:// or postgres://
    db_uri = db_uri.replace('postgresql+asyncpg://', 'postgresql://')

    print("Waiting for database to be ready...")

    for attempt in range(max_retries):
        try:
            conn = await asyncpg.connect(db_uri)
            await conn.close()
            print(" Database is ready!")
            return True
        except Exception as e:
            print(f" Attempt {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(delay)

    print(" Failed to connect to database after maximum retries")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(wait_for_db())

