from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    class Kind(models.TextChoices):
        EXPENSE = "expense", "Expense"
        INCOME = "income", "Income"
        BOTH = "both", "Both"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=80)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    icon = models.CharField(max_length=40, default="circle")
    color = models.CharField(max_length=16, default="#6B7280")
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.EXPENSE)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = ("user", "parent", "name")
        verbose_name_plural = "categories"
        indexes = [models.Index(fields=["user", "kind"])]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"
        TRANSFER = "transfer", "Transfer"

    class Status(models.TextChoices):
        CLEARED = "cleared", "Cleared"
        PENDING = "pending", "Pending"
        VOID = "void", "Void"

    class Method(models.TextChoices):
        CARD = "card", "Card"
        CASH = "cash", "Cash"
        BANK = "bank", "Bank transfer"
        WALLET = "wallet", "Wallet"
        OTHER = "other", "Other"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(
        "finance_accounts.Account", on_delete=models.PROTECT, related_name="transactions"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = models.CharField(max_length=12, choices=Type.choices)
    merchant = models.CharField(max_length=160, blank=True)
    description = models.CharField(max_length=255, blank=True)
    transaction_date = models.DateField()
    notes = models.TextField(blank=True)
    currency = models.CharField(max_length=8, default=settings.DEFAULT_CURRENCY)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CLEARED)
    payment_method = models.CharField(max_length=12, choices=Method.choices, default=Method.OTHER)
    transfer = models.ForeignKey(
        "finance_accounts.Transfer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    tags = models.ManyToManyField("core.Tag", through="TransactionTag", blank=True, related_name="transactions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-transaction_date", "-id"]
        indexes = [
            models.Index(fields=["user", "transaction_date"]),
            models.Index(fields=["user", "transaction_type"]),
            models.Index(fields=["user", "category"]),
            models.Index(fields=["user", "account"]),
            models.Index(fields=["user", "merchant"]),
        ]

    def __str__(self):
        return f"{self.transaction_type} {self.amount} {self.merchant or self.description}"


class TransactionTag(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    tag = models.ForeignKey("core.Tag", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("transaction", "tag")


class Receipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receipts")
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="receipts"
    )
    image = models.ImageField(upload_to="receipts/")
    thumbnail = models.ImageField(upload_to="receipts/thumbs/", blank=True, null=True)
    original_name = models.CharField(max_length=255, blank=True)
    ocr_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
