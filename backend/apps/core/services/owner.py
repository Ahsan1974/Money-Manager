import os
import secrets

from django.contrib.auth.models import User

from apps.core.services.defaults import ensure_user_defaults


def get_or_create_owner() -> User:
    user = User.objects.order_by("pk").first()
    if user:
        return user

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
    return user
