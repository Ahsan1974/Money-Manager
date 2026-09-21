from rest_framework import serializers

from apps.budgets.models import Budget, BudgetCategory


class BudgetCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)

    class Meta:
        model = BudgetCategory
        fields = [
            "id",
            "category",
            "category_name",
            "category_icon",
            "category_color",
            "allocated_amount",
        ]


class BudgetSerializer(serializers.ModelSerializer):
    items = BudgetCategorySerializer(many=True)

    class Meta:
        model = Budget
        fields = ["id", "name", "year", "month", "notes", "items", "created_at"]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        budget = Budget.objects.create(user=self.context["request"].user, **validated_data)
        for item in items:
            BudgetCategory.objects.create(budget=budget, **item)
        return budget

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for item in items:
                BudgetCategory.objects.create(budget=instance, **item)
        return instance
