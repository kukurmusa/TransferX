web: python src/manage.py migrate --noinput && python src/manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
