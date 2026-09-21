from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class UserScopedMixin:
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserScopedViewSet(UserScopedMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
