#!/bin/bash
set -e
echo "=== Starting TransferX ==="
echo "=== Working directory: $(pwd) ==="
echo "=== Python path: $(which python) ==="
cd /app
echo "=== Collecting static files ==="
python src/manage.py collectstatic --noinput
echo "=== Running migrations ==="
python src/manage.py migrate
echo "=== Starting gunicorn ==="
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --chdir src
