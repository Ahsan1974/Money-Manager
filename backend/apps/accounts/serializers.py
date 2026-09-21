from django.contrib.auth.models import User
from rest_framework import serializers

from apps.accounts.models import Account, Investment, Transfer
from apps.core.services.ledger import create_transfer, delete_transfer
from apps.core.services.money import money


class AccountSerializer(serializers.ModelSerializer):
    is_liability = serializers.BooleanField(read_only=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "institution",
            "account_type",
            "opening_balance",
            "current_balance",
            "currency",
            "color",
            "icon",
            "notes",
            "is_archived",
            "include_in_net_worth",
            "include_in_safe_to_spend",
            "sort_order",
            "is_liability",
            "created_at",
        ]
        read_only_fields = ["current_balance", "created_at"]

    def create(self, validated_data):
        opening = money(validated_data.get("opening_balance") or 0)
        validated_data["current_balance"] = opening
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class TransferSerializer(serializers.ModelSerializer):
    from_account_name = serializers.CharField(source="from_account.name", read_only=True)
    to_account_name = serializers.CharField(source="to_account.name", read_only=True)

    class Meta:
        model = Transfer
        fields = [
            "id",
            "from_account",
            "to_account",
            "from_account_name",
            "to_account_name",
            "amount",
            "fee",
            "transfer_date",
            "notes",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        if attrs.get("from_account") and attrs.get("to_account"):
            if attrs["from_account"].id == attrs["to_account"].id:
                raise serializers.ValidationError("Choose two different accounts.")
            user = self.context["request"].user
            if attrs["from_account"].user_id != user.id or attrs["to_account"].user_id != user.id:
                raise serializers.ValidationError("Accounts not found.")
        return attrs

    def create(self, validated_data):
        return create_transfer(user=self.context["request"].user, **validated_data)


class InvestmentSerializer(serializers.ModelSerializer):
    gain = serializers.SerializerMethodField()

    class Meta:
        model = Investment
        fields = [
            "id",
            "name",
            "investment_type",
            "amount_invested",
            "current_value",
            "purchased_on",
            "account",
            "notes",
            "gain",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_gain(self, obj):
        return str(obj.gain)

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
