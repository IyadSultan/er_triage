"""
Django settings for the ER Triage Extractor — CCI Session 11.

This is the "ready-made app" students tour in Lesson 5, extend in Lesson 6,
and deploy to Render in Lesson 7. It is deliberately written to run out of the
box: SQLite by default, sensible dev fallbacks for every secret, and graceful
degradation when no OpenAI key is present.

Production knobs (DEBUG, ALLOWED_HOSTS, SECRET_KEY, the LLM key, the encryption
keys) are all read from environment variables / a .env file. See .env.example.
"""
from pathlib import Path
import os

# --- load a local .env if present (python-dotenv) ---------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv is optional; env vars still work without it
    pass


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


BASE_DIR = Path(__file__).resolve().parent.parent

# --- core -------------------------------------------------------------------
# A dev SECRET_KEY ships so the app runs immediately. In production Render sets
# a real one as an environment variable.
SECRET_KEY = os.environ.get("SECRET_KEY") or (
    "django-insecure-cci-session-11-dev-key-change-in-production"
)

DEBUG = _env_bool("DEBUG", default=True)

# ALLOWED_HOSTS: comma-separated env var in production. Render injects the host
# name as RENDER_EXTERNAL_HOSTNAME, which we add automatically.
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if "." in h]

# --- apps -------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # --- our apps ---
    "triage",
    # Lesson 6 adds a new app on the line below:
    # "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves static files in production without a separate web server.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "er_triage.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "er_triage.wsgi.application"

# --- database ---------------------------------------------------------------
# SQLite by default — zero config, and good enough for the capstone AND for a
# small Render deployment (point a Render persistent disk at the file). If you
# would rather use Render's managed Postgres, set DATABASE_URL and dj-database-url
# will pick it up automatically.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SQLITE_PATH", BASE_DIR / "db.sqlite3"),
    }
}
_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    try:
        import dj_database_url

        DATABASES["default"] = dj_database_url.parse(_database_url, conn_max_age=600)
    except ImportError:
        pass  # fall back to SQLite if dj-database-url isn't installed

# --- auth / i18n / static ---------------------------------------------------
AUTH_PASSWORD_VALIDATORS = []  # no auth in v1 (hospital SSO is a v2 concern)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Amman"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
