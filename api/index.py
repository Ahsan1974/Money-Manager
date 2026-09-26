import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

django_app = get_wsgi_application()

_started = False


def _ensure_schema():
    global _started
    if _started or not os.getenv("VERCEL") or not os.getenv("DATABASE_URL"):
        return
    _started = True
    marker = Path("/tmp/monea-migrated")
    if marker.exists():
        return
    try:
        from django.core.management import call_command

        call_command("migrate", interactive=False, verbosity=0)
        if os.getenv("OWNER_PASSWORD"):
            call_command("seed_demo", verbosity=0)
        marker.write_text("ok")
    except Exception as exc:
        _started = False
        print(f"startup migrate/seed failed: {exc}", flush=True)


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
    path = _original_path(environ)
    if not path.startswith("/api/healthz"):
        _ensure_schema()
    environ["PATH_INFO"] = path
    environ["SCRIPT_NAME"] = ""
    return django_app(environ, start_response)
