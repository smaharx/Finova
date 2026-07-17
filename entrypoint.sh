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
    conn_str = os.environ.get('DATABASE_URL')
    # psycopg2 accepts both DSN and URL form
    psycopg2.connect(conn_str)
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

# Download model if MODEL_URL is provided and model file is missing
if [ ! -f "ml/saved_brain.pkl" ] && [ -n "$MODEL_URL" ]; then
  echo "MODEL_URL provided and ml/saved_brain.pkl missing — downloading model..."
  python - <<PY
import os, sys, urllib.request
url = os.environ.get('MODEL_URL')
if not url:
    print('MODEL_URL not set')
    sys.exit(0)
os.makedirs('ml', exist_ok=True)
out_path = os.path.join('ml', 'saved_brain.pkl')
try:
    urllib.request.urlretrieve(url, out_path)
    print('Model downloaded to', out_path)
except Exception as e:
    print('Model download failed:', e)
    sys.exit(1)
PY
fi

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the app
exec uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
