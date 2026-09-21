from django.contrib.auth.models import User
from django.db import models


class Debt(models.Model):
    class Kind(models.TextChoices):
        CREDIT_CARD = "credit_card", "Credit card"
        LOAN = "loan", "Loan"
        INSTALLMENT = "installment", "Installment"
        PERSONAL = "personal", "Personal debt"
        OTHER = "other", "Other"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="debts")
    name = models.CharField(max_length=160)
    debt_type = models.CharField(max_length=20, choices=Kind.choices, default=Kind.LOAN)
    original_amount = models.DecimalField(max_digits=14, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=14, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    due_day = models.PositiveSmallIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    linked_account = models.ForeignKey(
        "finance_accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="debts",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DebtPayment(models.Model):
    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_on = models.DateField()
    account = models.ForeignKey(
        "finance_accounts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="debt_payments",
    )
    notes = models.TextField(blank=True)
    transaction = models.ForeignKey(
        "transactions.Transaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="debt_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-id"]


class LendingRecord(models.Model):
    class Direction(models.TextChoices):
        LENT = "lent", "I lent"
        BORROWED = "borrowed", "I borrowed"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PARTIAL = "partial", "Partial"
        SETTLED = "settled", "Settled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lending_records")
    person = models.ForeignKey("core.Person", on_delete=models.PROTECT, related_name="lending_records")
    direction = models.CharField(max_length=12, choices=Direction.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=14, decimal_places=2)
    record_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    expected_repayment = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "expected_repayment", "-record_date"]
        indexes = [models.Index(fields=["user", "direction", "status"])]


class LendingPayment(models.Model):
    record = models.ForeignKey(LendingRecord, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_on = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-id"]
