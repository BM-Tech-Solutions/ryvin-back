#!/bin/sh
set -e

# Get the first argument which should be the service name
SERVICE_TYPE=$1

# Wait for Postgres to be ready (simple and robust)
echo "Waiting for database to be ready..."
python - << 'PY'
import os, time, sys
from sqlalchemy import create_engine, text
uri = os.environ.get('DATABASE_URI') or (
    f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@"
    f"{os.environ.get('POSTGRES_SERVER','db')}:{os.environ.get('POSTGRES_PORT','5432')}/"
    f"{os.environ.get('POSTGRES_DB')}"
)
for i in range(60):
    try:
        eng = create_engine(uri, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database is ready.")
        sys.exit(0)
    except Exception as e:
        print(f"Waiting for DB... ({i+1}/60): {e}")
        time.sleep(2)
print("Database did not become ready in time.")
sys.exit(1)
PY
if [ $? -ne 0 ]; then
  echo "Exiting because database is not ready."
  exit 1
fi

# Run migrations only if this is the migrations service
if [ "$SERVICE_TYPE" = "migrations" ]; then
  echo "Running database migrations..."
  alembic upgrade head
  echo "Migrations completed successfully!"
  exit 0
fi

# For the web service, just start the application
echo "Starting application..."
exec "$@"
