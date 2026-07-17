#!/usr/bin/env bash
set -e

# Wait for DB
echo "Waiting for database..."
for i in {1..30}; do
  python - <<PY
import sys
import os
import psycopg2
try:
    psycopg2.connect(os.environ.get('DATABASE_URL'))
    print('DB ok')
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  if [ $? -eq 0 ]; then
    break
  fi
  sleep 1
done

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the app
exec uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
