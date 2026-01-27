import time
import psycopg2
import os

dsn = os.getenv("DATABASE_URI")

while True:
    try:
        conn = psycopg2.connect(dsn)
        conn.close()
        print("Database is ready!")
        break
    except psycopg2.OperationalError:
        print("Waiting for Postgres...")
        time.sleep(2)

