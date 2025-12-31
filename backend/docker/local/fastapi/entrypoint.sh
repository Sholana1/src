#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

python << END
import time
import sys
import psycopg

MAX_WAIT_SECONDS = 90
RETRY_INTERVAL = 5
start_time = time.time()

def check_database():
    try:
        conn = psycopg.connect(
            dbname="${POSTGRES_DB}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}",
        )
        conn.close()
        return True
    except psycopg.OperationalError as e:
        elapsed = int(time.time() - start_time)
        sys.stderr.write(f"Database not ready, retrying... ({elapsed}s elapsed)\n")
        return False

while True:
    if check_database():
        break
    if time.time() - start_time > MAX_WAIT_SECONDS:
        sys.stderr.write("Timed out waiting for the database to be ready.\n")
        sys.exit(1)
    sys.stdout.write("Waiting for the database to be ready...\n")
    time.sleep(RETRY_INTERVAL)
END

>&2 echo "Database is ready. Starting the application..."

alembic upgrade head
exec "$@"
