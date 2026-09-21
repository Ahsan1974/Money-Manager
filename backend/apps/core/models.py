from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    THEME_CHOICES = [
        ("system", "System"),
        ("light", "Light"),
        ("dark", "Dark"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    currency = models.CharField(max_length=8, default=settings.DEFAULT_CURRENCY)
    currency_symbol = models.CharField(max_length=8, default=settings.DEFAULT_CURRENCY_SYMBOL)
    theme = models.CharField(max_length=12, choices=THEME_CHOICES, default="system")
    hide_balance = models.BooleanField(default=False)

    pin_hash = models.CharField(max_length=128, blank=True)
    pin_enabled = models.BooleanField(default=False)
    lock_after_minutes = models.PositiveSmallIntegerField(default=2)

    emergency_reserve = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    savings_reserve = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    obligation_horizon_days = models.PositiveSmallIntegerField(default=30)
    include_upcoming_bills = models.BooleanField(default=True)
    include_debt_payments = models.BooleanField(default=True)
    include_goal_reserves = models.BooleanField(default=True)
    daily_spending_period_days = models.PositiveSmallIntegerField(default=30)

    notify_bills = models.BooleanField(default=True)
    notify_budgets = models.BooleanField(default=True)
    notify_subscriptions = models.BooleanField(default=True)
    notify_goals = models.BooleanField(default=True)
    notify_unusual = models.BooleanField(default=True)

    ai_enabled = models.BooleanField(default=True)
    first_day_of_week = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or self.user.get_username()


class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=40)
    color = models.CharField(max_length=16, default="#6B7280")

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="people")
    name = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("user", "name")

    def __str__(self):
        return self.name


class Notification(models.Model):
    class Kind(models.TextChoices):
        BILL = "bill", "Bill"
        BUDGET = "budget", "Budget"
        SUBSCRIPTION = "subscription", "Subscription"
        GOAL = "goal", "Goal"
        SPENDING = "spending", "Spending"
        REPORT = "report", "Report"
        LENDING = "lending", "Lending"
        SYSTEM = "system", "System"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.SYSTEM)
    title = models.CharField(max_length=160)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]


class FinancialRule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="financial_rules")
    name = models.CharField(max_length=120)
    rule_type = models.CharField(max_length=40)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]


class ImportSession(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        MAPPED = "mapped", "Mapped"
        PREVIEWED = "previewed", "Previewed"
        IMPORTED = "imported", "Imported"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="import_sessions")
    file = models.FileField(upload_to="imports/")
    original_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    detected_columns = models.JSONField(default=list, blank=True)
    mapping = models.JSONField(default=dict, blank=True)
    preview = models.JSONField(default=list, blank=True)
    result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class CurrencyRate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="currency_rates")
    base = models.CharField(max_length=8, default="PKR")
    quote = models.CharField(max_length=8)
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "base", "quote")
