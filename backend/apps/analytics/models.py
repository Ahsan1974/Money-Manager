from django.contrib.auth.models import User
from django.db import models


class NetWorthSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="net_worth_snapshots")
    snapshot_date = models.DateField()
    assets = models.DecimalField(max_digits=14, decimal_places=2)
    liabilities = models.DecimalField(max_digits=14, decimal_places=2)
    net_worth = models.DecimalField(max_digits=14, decimal_places=2)
    breakdown = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "snapshot_date")
        ordering = ["snapshot_date"]
        indexes = [models.Index(fields=["user", "snapshot_date"])]
