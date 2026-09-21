from django.contrib.auth.models import User
from django.db import models


class Frequency(models.TextChoices):
    ONCE = "once", "Once"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class Bill(models.Model):
    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        DUE_SOON = "due_soon", "Due soon"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        SKIPPED = "skipped", "Skipped"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bills")
    name = models.CharField(max_length=160)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    due_date = models.DateField()
    frequency = models.CharField(max_length=12, choices=Frequency.choices, default=Frequency.MONTHLY)
    category = models.ForeignKey(
        "transactions.Category", on_delete=models.SET_NULL, null=True, blank=True, related_name="bills"
    )
    account = models.ForeignKey(
        "finance_accounts.Account", on_delete=models.SET_NULL, null=True, blank=True, related_name="bills"
    )
    reminder_days = models.PositiveSmallIntegerField(default=2)
    auto_create_transaction = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPCOMING)
    last_paid_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "name"]
        indexes = [
            models.Index(fields=["user", "due_date"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    name = models.CharField(max_length=160)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    billing_cycle = models.CharField(
        max_length=12, choices=Frequency.choices, default=Frequency.MONTHLY
    )
    next_billing_date = models.DateField()
    category = models.ForeignKey(
        "transactions.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    account = models.ForeignKey(
        "finance_accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_billing_date", "name"]

    def __str__(self):
        return self.name
