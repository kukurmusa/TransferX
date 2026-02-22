#\!/usr/bin/env sh
set -e

python scripts/wait_for_db.py
python src/manage.py migrate --noinput
python src/manage.py collectstatic --noinput

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn config.wsgi:application \n  --bind "0.0.0.0:${PORT:-8000}" \n  --workers "${GUNICORN_WORKERS:-2}" \n  --timeout "${GUNICORN_TIMEOUT:-120}"
