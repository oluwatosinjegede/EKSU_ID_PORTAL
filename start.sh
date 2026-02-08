#!/bin/bash
set -e

echo "-------------------------------------"
echo "Starting Django container bootstrap"
echo "-------------------------------------"

echo "runing Django shell command"
python manage.py selfheal_ids

# -------------------------------------------------
# 1. Run Migrations
# -------------------------------------------------
echo "Running migrations..."
python manage.py migrate --noinput

# -------------------------------------------------
# 2. Create / Repair Superuser (from env vars)
# Requires: bootstrap_admin management command
# -------------------------------------------------
echo "Ensuring superuser exists..."
python manage.py bootstrap_admin || true

# -------------------------------------------------
# 3. Collect Static Files
# -------------------------------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput

# -------------------------------------------------
# 4. Import Students (Self-healing, safe)
# -------------------------------------------------
echo "Importing students..."
IMPORT_STUDENTS=true python manage.py import_students || true

# -------------------------------------------------
# 5. Start Gunicorn
# -------------------------------------------------
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
