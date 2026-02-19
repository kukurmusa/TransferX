import os
import time
import psycopg


def env(name, default=None):
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def main():
    dbname = env("POSTGRES_DB")
    user = env("POSTGRES_USER")
    password = env("POSTGRES_PASSWORD")
    host = env("POSTGRES_HOST", "db")
    port = env("POSTGRES_PORT", "5432")
    retries = int(os.getenv("DB_CONNECT_RETRIES", "30"))
    delay = float(os.getenv("DB_CONNECT_DELAY", "1"))

    dsn = f"dbname={dbname} user={user} password={password} host={host} port={port}"

    for attempt in range(1, retries + 1):
        try:
            with psycopg.connect(dsn) as conn:
                conn.execute("SELECT 1")
            return 0
        except Exception:
            if attempt == retries:
                break
            time.sleep(delay)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
