from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.core.services.owner import get_or_create_owner


class JWTOrOwnerAuthentication(BaseAuthentication):
    """Use a JWT when it is valid; otherwise open the single owner workspace."""

    def authenticate(self, request):
        try:
            result = JWTAuthentication().authenticate(request)
            if result:
                return result
        except Exception:
            pass
        return (get_or_create_owner(), "owner")
