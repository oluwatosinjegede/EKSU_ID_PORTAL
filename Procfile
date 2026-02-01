#web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
web: python manage.py migrate && python manage.py bootstrap_admin && gunicorn config.wsgi:application
