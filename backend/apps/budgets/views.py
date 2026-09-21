from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.budgets.models import Budget
from apps.budgets.serializers import BudgetSerializer
from apps.core.services.dashboard import _budget_progress, serialize_decimal
from django.utils import timezone


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    queryset = Budget.objects.all()
    filterset_fields = ["year", "month"]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).prefetch_related("items__category")

    @action(detail=False, methods=["get"])
    def current(self, request):
        today = timezone.localdate()
        year = int(request.query_params.get("year") or today.year)
        month = int(request.query_params.get("month") or today.month)
        data = _budget_progress(request.user, year, month, today)
        return Response(serialize_decimal(data) if data else {"items": []})
