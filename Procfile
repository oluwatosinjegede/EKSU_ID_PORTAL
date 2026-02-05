python manage.py migrate && \
python manage.py collectstatic --noinput && \
python manage.py import_students && \
gunicorn config.wsgi:application
