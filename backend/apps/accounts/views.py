from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Account, Investment, Transfer
from apps.accounts.serializers import AccountSerializer, InvestmentSerializer, TransferSerializer
from apps.core.services.ledger import delete_transfer, month_bounds
from apps.core.services.money import ZERO, money
from apps.transactions.models import Transaction
from django.db.models import Sum


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    queryset = Account.objects.all()
    search_fields = ["name", "institution"]
    filterset_fields = ["account_type", "is_archived"]
    pagination_class = None

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        account = self.get_object()
        year = int(request.query_params.get("year") or 0)
        month = int(request.query_params.get("month") or 0)
        qs = Transaction.objects.filter(account=account, status=Transaction.Status.CLEARED)
        if year and month:
            start, end = month_bounds(year, month)
            qs = qs.filter(transaction_date__gte=start, transaction_date__lte=end)
        income = money(qs.filter(transaction_type=Transaction.Type.INCOME).aggregate(t=Sum("amount"))["t"] or ZERO)
        expenses = money(qs.filter(transaction_type=Transaction.Type.EXPENSE).aggregate(t=Sum("amount"))["t"] or ZERO)
        trend = []
        if year and month:
            from apps.core.services.dashboard import _spending_series

            # Account-level monthly trend for last 6 months
            from datetime import date

            from apps.core.services.ledger import month_bounds as bounds

            def shift(y, m, d):
                m += d
                while m < 1:
                    m += 12
                    y -= 1
                while m > 12:
                    m -= 12
                    y += 1
                return y, m

            for offset in range(5, -1, -1):
                y, m = shift(year, month, -offset)
                s, e = bounds(y, m)
                month_qs = Transaction.objects.filter(
                    account=account,
                    transaction_date__gte=s,
                    transaction_date__lte=e,
                    status=Transaction.Status.CLEARED,
                )
                trend.append(
                    {
                        "label": date(y, m, 1).strftime("%b"),
                        "income": str(
                            money(month_qs.filter(transaction_type=Transaction.Type.INCOME).aggregate(t=Sum("amount"))["t"] or ZERO)
                        ),
                        "expenses": str(
                            money(month_qs.filter(transaction_type=Transaction.Type.EXPENSE).aggregate(t=Sum("amount"))["t"] or ZERO)
                        ),
                    }
                )
        return Response(
            {
                "id": account.id,
                "name": account.name,
                "current_balance": str(account.current_balance),
                "income": str(income),
                "expenses": str(expenses),
                "trend": trend,
                "is_liability": account.is_liability,
            }
        )


class TransferViewSet(viewsets.ModelViewSet):
    serializer_class = TransferSerializer
    queryset = Transfer.objects.all()
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return Transfer.objects.filter(user=self.request.user).select_related("from_account", "to_account")

    def perform_destroy(self, instance):
        delete_transfer(instance)


class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer
    queryset = Investment.objects.all()

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user)
