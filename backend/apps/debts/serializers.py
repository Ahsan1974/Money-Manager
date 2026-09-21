from rest_framework import serializers

from apps.core.services.money import ZERO, money
from apps.debts.models import Debt, DebtPayment, LendingPayment, LendingRecord


class DebtPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtPayment
        fields = ["id", "amount", "paid_on", "account", "notes", "created_at"]
        read_only_fields = ["created_at"]


class DebtSerializer(serializers.ModelSerializer):
    payments = DebtPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Debt
        fields = [
            "id",
            "name",
            "debt_type",
            "original_amount",
            "remaining_amount",
            "interest_rate",
            "monthly_payment",
            "due_day",
            "start_date",
            "end_date",
            "linked_account",
            "notes",
            "is_active",
            "payments",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        if "remaining_amount" not in validated_data:
            validated_data["remaining_amount"] = validated_data.get("original_amount")
        return super().create(validated_data)


class LendingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LendingPayment
        fields = ["id", "amount", "paid_on", "notes", "created_at"]
        read_only_fields = ["created_at"]


class LendingRecordSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source="person.name", read_only=True)
    payments = LendingPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = LendingRecord
        fields = [
            "id",
            "person",
            "person_name",
            "direction",
            "amount",
            "remaining_amount",
            "record_date",
            "reason",
            "expected_repayment",
            "status",
            "notes",
            "payments",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        if "remaining_amount" not in validated_data:
            validated_data["remaining_amount"] = validated_data.get("amount")
        return super().create(validated_data)
