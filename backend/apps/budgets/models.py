from django.contrib.auth.models import User
from django.db import models


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    name = models.CharField(max_length=80, default="Monthly budget")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "year", "month")
        ordering = ["-year", "-month"]
        indexes = [models.Index(fields=["user", "year", "month"])]

    def __str__(self):
        return f"{self.name} {self.year}-{self.month:02d}"


class BudgetCategory(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(
        "transactions.Category", on_delete=models.CASCADE, related_name="budget_items"
    )
    allocated_amount = models.DecimalField(max_digits=14, decimal_places=2)
    alert_75_sent = models.BooleanField(default=False)
    alert_90_sent = models.BooleanField(default=False)
    alert_100_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = ("budget", "category")
        ordering = ["category__sort_order", "category__name"]
