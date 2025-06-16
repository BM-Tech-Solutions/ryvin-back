#!/bin/sh

set -e

# Wait for the database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_SERVER $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

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
