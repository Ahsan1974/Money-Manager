from django.contrib.auth.models import User
from django.db import models


class SavingsGoal(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)
    icon = models.CharField(max_length=40, default="piggy-bank")
    color = models.CharField(max_length=16, default="#1B7A4E")
    notes = models.TextField(blank=True)
    is_reserved = models.BooleanField(default=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    linked_account = models.ForeignKey(
        "finance_accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goals",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "target_date", "name"]

    def __str__(self):
        return self.name


class GoalContribution(models.Model):
    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    contributed_on = models.DateField()
    account = models.ForeignKey(
        "finance_accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goal_contributions",
    )
    notes = models.TextField(blank=True)
    transaction = models.ForeignKey(
        "transactions.Transaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goal_contributions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-contributed_on", "-id"]
