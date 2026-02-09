#!/bin/bash
set -e

echo "-------------------------------------"
echo "Starting Django container bootstrap"
echo "-------------------------------------"

# -------------------------------------------------
# 1. Run Migrations FIRST (CRITICAL)
# -------------------------------------------------
echo "Running migrations..."
python manage.py migrate --noinput || {
  echo "Migration failed — stopping container"
  exit 1
}


# -------------------------------------------------
# 2. Self-heal IDs (now DB schema is safe)
# -------------------------------------------------
echo "Running ID self-heal..."
python manage.py selfheal_ids || true

# -------------------------------------------------
# 3. Create / Repair Superuser
# -------------------------------------------------
echo "Ensuring superuser exists..."
python manage.py bootstrap_admin || true

# -------------------------------------------------
# 4. Collect Static Files
# -------------------------------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput

# -------------------------------------------------
# 5. Import Students (optional safe)
# -------------------------------------------------
echo "Importing students..."
IMPORT_STUDENTS=true python manage.py import_students || true

# -------------------------------------------------
# 6. Start Gunicorn
# -------------------------------------------------
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
