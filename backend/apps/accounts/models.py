from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

LIABILITY_TYPES = {"credit_card"}


class Account(models.Model):
    class Type(models.TextChoices):
        BANK = "bank", "Bank account"
        CASH = "cash", "Cash"
        CREDIT_CARD = "credit_card", "Credit card"
        SAVINGS = "savings", "Savings account"
        WALLET = "wallet", "Digital wallet"
        INVESTMENT = "investment", "Investment account"
        OTHER = "other", "Other"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=120)
    institution = models.CharField(max_length=120, blank=True)
    account_type = models.CharField(max_length=20, choices=Type.choices, default=Type.BANK)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default=settings.DEFAULT_CURRENCY)
    color = models.CharField(max_length=16, default="#1B7A4E")
    icon = models.CharField(max_length=40, default="wallet")
    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    include_in_net_worth = models.BooleanField(default=True)
    include_in_safe_to_spend = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["user", "account_type"]),
            models.Index(fields=["user", "is_archived"]),
        ]

    def __str__(self):
        return self.name

    @property
    def is_liability(self) -> bool:
        return self.account_type in LIABILITY_TYPES


class Transfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transfers")
    from_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="transfers_out"
    )
    to_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="transfers_in"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    fee = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    transfer_date = models.DateField()
    notes = models.TextField(blank=True)
    from_transaction = models.OneToOneField(
        "transactions.Transaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfer_out_link",
    )
    to_transaction = models.OneToOneField(
        "transactions.Transaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfer_in_link",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transfer_date", "-id"]


class Investment(models.Model):
    class Kind(models.TextChoices):
        STOCK = "stock", "Stock"
        FUND = "fund", "Fund"
        BOND = "bond", "Bond"
        SAVINGS_CERT = "savings_cert", "Savings certificate"
        GOLD = "gold", "Gold"
        OTHER = "other", "Other"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="investments")
    name = models.CharField(max_length=160)
    investment_type = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    amount_invested = models.DecimalField(max_digits=14, decimal_places=2)
    current_value = models.DecimalField(max_digits=14, decimal_places=2)
    purchased_on = models.DateField()
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="investments"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-purchased_on"]

    @property
    def gain(self):
        from apps.core.services.money import money

        return money(self.current_value) - money(self.amount_invested)
