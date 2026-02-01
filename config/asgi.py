"""
ASGI config for Django project.

It exposes the ASGI callable as a module-level variable named ``application``.

Used for async features (WebSockets, SSE, etc.).
"""

import os
from django.core.asgi import get_asgi_application

# IMPORTANT: must match your project folder name
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
