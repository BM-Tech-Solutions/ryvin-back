#!/bin/sh
set -e

# Get the first argument which should be the service name
SERVICE_TYPE=$1

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
