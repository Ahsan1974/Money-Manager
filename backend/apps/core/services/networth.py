from datetime import date

from apps.accounts.models import Account, Investment
from apps.analytics.models import NetWorthSnapshot
from apps.core.services.money import ZERO, money
from apps.debts.models import Debt, LendingRecord


def compute_net_worth(user) -> dict:
    assets = ZERO
    liabilities = ZERO
    asset_items = []
    liability_items = []

    for account in Account.objects.filter(user=user, is_archived=False, include_in_net_worth=True):
        balance = money(account.current_balance)
        if account.is_liability:
            liabilities += balance
            liability_items.append({"name": account.name, "amount": str(balance), "kind": "account"})
        else:
            assets += balance
            asset_items.append({"name": account.name, "amount": str(balance), "kind": "account"})

    counted_accounts = {
        debt.linked_account_id
        for debt in Debt.objects.filter(user=user, is_active=True, linked_account__isnull=False)
    }
    for debt in Debt.objects.filter(user=user, is_active=True):
        if debt.linked_account_id and debt.linked_account_id in counted_accounts:
            # Already represented as a credit-card (or other) account.
            if debt.linked_account and debt.linked_account.is_liability:
                continue
        remaining = money(debt.remaining_amount)
        liabilities += remaining
        liability_items.append({"name": debt.name, "amount": str(remaining), "kind": "debt"})

    for inv in Investment.objects.filter(user=user):
        if inv.account_id:
            continue
        value = money(inv.current_value)
        assets += value
        asset_items.append({"name": inv.name, "amount": str(value), "kind": "investment"})

    owed_to_me = ZERO
    i_owe = ZERO
    for record in LendingRecord.objects.filter(user=user).exclude(status=LendingRecord.Status.SETTLED):
        remaining = money(record.remaining_amount)
        if record.direction == LendingRecord.Direction.LENT:
            owed_to_me += remaining
        else:
            i_owe += remaining
    assets += owed_to_me
    liabilities += i_owe
    if owed_to_me:
        asset_items.append({"name": "Money lent", "amount": str(owed_to_me), "kind": "lending"})
    if i_owe:
        liability_items.append({"name": "Money borrowed", "amount": str(i_owe), "kind": "lending"})

    net = money(assets - liabilities)
    return {
        "assets": assets,
        "liabilities": liabilities,
        "net_worth": net,
        "breakdown": {
            "assets": asset_items,
            "liabilities": liability_items,
        },
    }


def snapshot_net_worth(user, snapshot_date: date | None = None) -> NetWorthSnapshot:
    snapshot_date = snapshot_date or date.today()
    data = compute_net_worth(user)
    obj, _ = NetWorthSnapshot.objects.update_or_create(
        user=user,
        snapshot_date=snapshot_date,
        defaults={
            "assets": data["assets"],
            "liabilities": data["liabilities"],
            "net_worth": data["net_worth"],
            "breakdown": data["breakdown"],
        },
    )
    return obj
