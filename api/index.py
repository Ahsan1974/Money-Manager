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
    except Exception:
        pass


def app(environ, start_response):
    uri = environ.get("REQUEST_URI") or environ.get("RAW_URI") or ""
    path = uri.split("?", 1)[0] if uri else environ.get("PATH_INFO", "")
    forwarded = environ.get("HTTP_X_FORWARDED_URI") or environ.get("HTTP_X_INVOKE_PATH") or ""
    if forwarded:
        path = forwarded.split("?", 1)[0]
    if path and not path.startswith("/api") and not path.startswith("/admin") and not path.startswith("/media"):
        path = "/api" + (path if path.startswith("/") else "/" + path)
    if path:
        environ["PATH_INFO"] = path
    return django_app(environ, start_response)
