"""
WSGI config for Django project.

It exposes the WSGI callable as a module-level variable named ``application``.

This file is used by Gunicorn in production (Railway).
"""

import os
from django.core.wsgi import get_wsgi_application

# IMPORTANT: must match your project folder name
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
