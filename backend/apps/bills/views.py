from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bills.models import Bill, Subscription
from apps.bills.serializers import BillSerializer, SubscriptionSerializer
from apps.core.services.money import ZERO, money
from apps.core.services.recurring import pay_bill, refresh_bill_statuses


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.all()
    filterset_fields = ["status", "is_active"]

    def get_queryset(self):
        refresh_bill_statuses(self.request.user)
        return Bill.objects.filter(user=self.request.user).select_related("category", "account")

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        bill = self.get_object()
        create_tx = str(request.data.get("create_transaction", "true")).lower() != "false"
        pay_bill(bill, create_tx=create_tx)
        return Response(BillSerializer(bill, context={"request": request}).data)

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        bills = self.get_queryset().exclude(status__in=[Bill.Status.PAID, Bill.Status.SKIPPED])
        payload = [
            {
                "id": bill.id,
                "name": bill.name,
                "amount": str(bill.amount),
                "due_date": bill.due_date.isoformat(),
                "status": bill.status,
            }
            for bill in bills
        ]
        return Response(payload)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()
    filterset_fields = ["status"]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        qs = self.get_queryset().filter(status=Subscription.Status.ACTIVE)
        monthly = ZERO
        largest = None
        items = []
        for sub in qs:
            serialized = SubscriptionSerializer(sub).data
            monthly += money(serialized["monthly_cost"])
            items.append(serialized)
            if largest is None or money(sub.price) > money(largest.price):
                largest = sub
        upcoming = qs.order_by("next_billing_date")[:5]
        return Response(
            {
                "monthly": str(money(monthly)),
                "annual": str(money(monthly * 12)),
                "active": qs.count(),
                "largest": largest.name if largest else None,
                "upcoming": SubscriptionSerializer(upcoming, many=True).data,
                "insight": f"You spend approximately Rs. {money(monthly):,.0f}/month on recurring subscriptions.",
            }
        )
