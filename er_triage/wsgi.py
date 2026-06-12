"""WSGI entrypoint — this is what Gunicorn imports on Render."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "er_triage.settings")

application = get_wsgi_application()
