python manage.py migrate && python manage.py collectstatic --noinput && python manage.py import_students || true && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
