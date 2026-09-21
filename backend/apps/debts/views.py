from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.models import Notification
from apps.core.services.ledger import create_transaction
from apps.core.services.money import ZERO, money
from apps.debts.models import Debt, DebtPayment, LendingPayment, LendingRecord
from apps.debts.serializers import (
    DebtPaymentSerializer,
    DebtSerializer,
    LendingPaymentSerializer,
    LendingRecordSerializer,
)
from apps.transactions.models import Transaction


class DebtViewSet(viewsets.ModelViewSet):
    serializer_class = DebtSerializer
    queryset = Debt.objects.all()

    def get_queryset(self):
        return Debt.objects.filter(user=self.request.user).prefetch_related("payments")

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        debt = self.get_object()
        serializer = DebtPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = money(serializer.validated_data["amount"])
        payment = DebtPayment.objects.create(debt=debt, **serializer.validated_data)
        debt.remaining_amount = money(debt.remaining_amount) - amount
        if debt.remaining_amount <= ZERO:
            debt.remaining_amount = ZERO
            debt.is_active = False
        debt.save(update_fields=["remaining_amount", "is_active", "updated_at"])
        account = serializer.validated_data.get("account")
        if account:
            # Paying a debt from an asset account is a transfer-like reduction, not lifestyle spend.
            # If the debt is linked to a credit-card account, record a transfer; otherwise expense.
            if debt.linked_account_id:
                from apps.core.services.ledger import create_transfer

                create_transfer(
                    user=request.user,
                    from_account=account,
                    to_account=debt.linked_account,
                    amount=amount,
                    transfer_date=serializer.validated_data["paid_on"],
                    notes=f"Payment toward {debt.name}",
                )
            else:
                tx = create_transaction(
                    user=request.user,
                    account=account,
                    amount=amount,
                    transaction_type=Transaction.Type.TRANSFER,
                    transaction_date=serializer.validated_data["paid_on"],
                    merchant=debt.name,
                    description=f"Debt payment — {debt.name}",
                    notes="Does not count as an expense.",
                    payment_method=Transaction.Method.BANK,
                )
                payment.transaction = tx
                payment.save(update_fields=["transaction"])
        return Response(DebtSerializer(debt, context={"request": request}).data)


class LendingViewSet(viewsets.ModelViewSet):
    serializer_class = LendingRecordSerializer
    queryset = LendingRecord.objects.all()
    filterset_fields = ["direction", "status"]

    def get_queryset(self):
        return LendingRecord.objects.filter(user=self.request.user).select_related("person").prefetch_related("payments")

    @action(detail=True, methods=["post"])
    def repay(self, request, pk=None):
        record = self.get_object()
        serializer = LendingPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = money(serializer.validated_data["amount"])
        LendingPayment.objects.create(record=record, **serializer.validated_data)
        record.remaining_amount = money(record.remaining_amount) - amount
        if record.remaining_amount <= ZERO:
            record.remaining_amount = ZERO
            record.status = LendingRecord.Status.SETTLED
        else:
            record.status = LendingRecord.Status.PARTIAL
        record.save(update_fields=["remaining_amount", "status", "updated_at"])
        return Response(LendingRecordSerializer(record, context={"request": request}).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = self.get_queryset().exclude(status=LendingRecord.Status.SETTLED)
        owed = ZERO
        borrowed = ZERO
        for rec in qs:
            if rec.direction == LendingRecord.Direction.LENT:
                owed += money(rec.remaining_amount)
            else:
                borrowed += money(rec.remaining_amount)
        return Response({"owed_to_me": str(owed), "i_owe": str(borrowed)})
