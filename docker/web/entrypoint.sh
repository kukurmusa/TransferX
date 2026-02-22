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
echo "=== Seeding demo users ==="
python src/manage.py seed_demo
echo "=== Resetting demo passwords ==="
python src/manage.py reset_demo_passwords
echo "=== Checking DB and auth ==="
python src/manage.py check_db
echo "=== Starting gunicorn ==="
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --chdir src
