"""ASGI entrypoint (unused by the Render Gunicorn setup, here for completeness)."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "er_triage.settings")

application = get_asgi_application()
