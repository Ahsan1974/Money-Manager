from rest_framework import serializers

from apps.core.services.money import ZERO, money
from apps.goals.models import GoalContribution, SavingsGoal


class GoalContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalContribution
        fields = ["id", "amount", "contributed_on", "account", "notes", "created_at"]
        read_only_fields = ["created_at"]


class SavingsGoalSerializer(serializers.ModelSerializer):
    remaining = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    required_monthly = serializers.SerializerMethodField()
    required_weekly = serializers.SerializerMethodField()
    contributions = GoalContributionSerializer(many=True, read_only=True)

    class Meta:
        model = SavingsGoal
        fields = [
            "id",
            "name",
            "target_amount",
            "current_amount",
            "target_date",
            "icon",
            "color",
            "notes",
            "is_reserved",
            "status",
            "linked_account",
            "remaining",
            "progress",
            "required_monthly",
            "required_weekly",
            "contributions",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def _remaining(self, obj):
        leftover = money(obj.target_amount) - money(obj.current_amount)
        return leftover if leftover > ZERO else ZERO

    def get_remaining(self, obj):
        return str(self._remaining(obj))

    def get_progress(self, obj):
        from apps.core.services.money import percent

        return str(percent(obj.current_amount, obj.target_amount))

    def _months_left(self, obj):
        from datetime import date

        if not obj.target_date:
            return 1
        today = date.today()
        months = (obj.target_date.year - today.year) * 12 + (obj.target_date.month - today.month)
        return max(months, 1)

    def get_required_monthly(self, obj):
        return str(money(self._remaining(obj) / self._months_left(obj)))

    def get_required_weekly(self, obj):
        months = self._months_left(obj)
        weeks = max(months * 4, 1)
        return str(money(self._remaining(obj) / weeks))

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
