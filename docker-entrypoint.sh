#!/bin/sh

set -e

# Wait for the database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_SERVER $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"
