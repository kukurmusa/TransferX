#!/usr/bin/env sh
set -e

python scripts/wait_for_db.py
python src/manage.py migrate --noinput

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec python src/manage.py runserver 0.0.0.0:8000
