import os
import secrets

from django.contrib.auth.models import User

_cached_owner = None


def get_or_create_owner() -> User:
    global _cached_owner
    if _cached_owner is not None:
        return _cached_owner

    user = User.objects.select_related("profile").order_by("pk").first()
    if user:
        _cached_owner = user
        return user

    from apps.core.services.defaults import ensure_user_defaults

    username = (os.getenv("OWNER_USERNAME") or "ahsan").strip()
    display_name = (os.getenv("OWNER_DISPLAY_NAME") or "Ahsan Nadeem").strip()
    password = os.getenv("OWNER_PASSWORD") or secrets.token_urlsafe(24)
    parts = display_name.split(" ", 1)
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=parts[0],
        last_name=parts[1] if len(parts) > 1 else "",
        email="ahsan@localhost",
    )
    user.profile.display_name = display_name
    user.profile.save()
    ensure_user_defaults(user)
    _cached_owner = user
    return user
