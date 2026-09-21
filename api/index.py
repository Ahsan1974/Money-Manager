import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()

if os.getenv("VERCEL") and os.getenv("DATABASE_URL"):
    try:
        from django.core.management import call_command

        call_command("migrate", interactive=False, verbosity=0)
        if os.getenv("OWNER_PASSWORD"):
            call_command("seed_demo", interactive=False, verbosity=0)
    except Exception:
        pass


def _original_path(environ) -> str:
    for key in (
        "HTTP_X_INVOKE_PATH",
        "HTTP_X_VERCEL_ORIGINAL_PATH",
        "HTTP_X_FORWARDED_URI",
        "HTTP_X_FORWARDED_PATH",
        "REQUEST_URI",
        "RAW_URI",
        "PATH_INFO",
    ):
        raw = environ.get(key) or ""
        path = raw.split("?", 1)[0]
        if path.startswith("/api") or path.startswith("/admin") or path.startswith("/media"):
            return path
    fallback = (environ.get("PATH_INFO") or "/").split("?", 1)[0]
    if fallback.startswith("/api"):
        return fallback
    return "/api" + (fallback if fallback.startswith("/") else "/" + fallback)


def app(environ, start_response):
    environ["PATH_INFO"] = _original_path(environ)
    environ["SCRIPT_NAME"] = ""
    return django_app(environ, start_response)
