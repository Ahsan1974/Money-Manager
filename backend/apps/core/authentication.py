from rest_framework.authentication import BaseAuthentication

from apps.core.services.owner import get_or_create_owner


class OwnerFallbackAuthentication(BaseAuthentication):
    """Personal workspace: if no JWT is present, use the single owner account."""

    def authenticate(self, request):
        return (get_or_create_owner(), "owner")
