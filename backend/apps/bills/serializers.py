from rest_framework import serializers

from apps.bills.models import Bill, Subscription
from apps.core.services.money import ZERO, money


class BillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "name",
            "amount",
            "due_date",
            "frequency",
            "category",
            "category_name",
            "account",
            "account_name",
            "reminder_days",
            "auto_create_transaction",
            "status",
            "last_paid_on",
            "notes",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    monthly_cost = serializers.SerializerMethodField()
    annual_cost = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "name",
            "price",
            "billing_cycle",
            "next_billing_date",
            "category",
            "category_name",
            "account",
            "status",
            "notes",
            "monthly_cost",
            "annual_cost",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def _monthly(self, obj):
        price = money(obj.price)
        if obj.billing_cycle == "yearly":
            return money(price / 12)
        if obj.billing_cycle == "weekly":
            from decimal import Decimal

            return money(price * Decimal("4.345"))
        return price

    def get_monthly_cost(self, obj):
        return str(self._monthly(obj))

    def get_annual_cost(self, obj):
        return str(money(self._monthly(obj) * 12))

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
