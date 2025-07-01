#!/bin/sh

# Change to the backend directory where alembic.ini is located
cd /app/backend

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Change back to the src directory and start the application
cd /app/backend/src
echo "Starting FastAPI application..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8080 