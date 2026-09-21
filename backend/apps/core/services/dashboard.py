from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.accounts.models import Account
from apps.bills.models import Bill, Subscription
from apps.budgets.models import Budget
from apps.core.models import Notification
from apps.core.services.ledger import month_bounds
from apps.core.services.money import ZERO, money, percent, savings_rate
from apps.core.services.networth import compute_net_worth, snapshot_net_worth
from apps.core.services.safe_to_spend import calculate_safe_to_spend, daily_allowance
from apps.goals.models import SavingsGoal
from apps.transactions.models import Category, Transaction


def _month_totals(user, start: date, end: date) -> dict:
    qs = Transaction.objects.filter(
        user=user,
        transaction_date__gte=start,
        transaction_date__lte=end,
        status=Transaction.Status.CLEARED,
    )
    income = money(
        qs.filter(transaction_type=Transaction.Type.INCOME).aggregate(t=Sum("amount"))["t"] or ZERO
    )
    expenses = money(
        qs.filter(transaction_type=Transaction.Type.EXPENSE).aggregate(t=Sum("amount"))["t"] or ZERO
    )
    saved = money(income - expenses)
    return {
        "income": income,
        "expenses": expenses,
        "saved": saved,
        "savings_rate": savings_rate(income, expenses),
    }


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    month += delta
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return year, month


def _greeting(now) -> str:
    hour = now.hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _spending_series(user, year: int, month: int) -> dict:
    start, end = month_bounds(year, month)
    expenses = (
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__gte=start,
            transaction_date__lte=end,
            status=Transaction.Status.CLEARED,
        )
        .values("transaction_date")
        .annotate(total=Sum("amount"))
    )
    by_day = {row["transaction_date"]: money(row["total"]) for row in expenses}
    daily = []
    cursor = start
    while cursor <= end:
        daily.append({"date": cursor.isoformat(), "amount": by_day.get(cursor, ZERO)})
        cursor += timedelta(days=1)

    weekly = []
    week_total = ZERO
    week_start = start
    for i, point in enumerate(daily, start=1):
        week_total += money(point["amount"])
        is_week_end = i % 7 == 0 or point["date"] == end.isoformat()
        if is_week_end:
            weekly.append(
                {
                    "label": f"W{len(weekly) + 1}",
                    "start": week_start.isoformat(),
                    "amount": week_total,
                }
            )
            week_total = ZERO
            week_start = date.fromisoformat(point["date"]) + timedelta(days=1)

    monthly = []
    for offset in range(5, -1, -1):
        y, m = _shift_month(year, month, -offset)
        s, e = month_bounds(y, m)
        total = (
            Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.Type.EXPENSE,
                transaction_date__gte=s,
                transaction_date__lte=e,
                status=Transaction.Status.CLEARED,
            ).aggregate(t=Sum("amount"))["t"]
            or ZERO
        )
        monthly.append({"label": date(y, m, 1).strftime("%b"), "year": y, "month": m, "amount": money(total)})
    return {"daily": daily, "weekly": weekly, "monthly": monthly}


def _category_breakdown(user, start: date, end: date):
    rows = (
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__gte=start,
            transaction_date__lte=end,
            status=Transaction.Status.CLEARED,
        )
        .values(
            "category_id",
            "category__name",
            "category__color",
            "category__icon",
            "category__parent_id",
            "category__parent__name",
        )
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    grouped = {}
    for row in rows:
        parent_id = row["category__parent_id"] or row["category_id"]
        parent_name = row["category__parent__name"] or row["category__name"] or "Uncategorized"
        color = row["category__color"] or "#6B7280"
        icon = row["category__icon"] or "circle"
        if parent_id not in grouped:
            grouped[parent_id] = {
                "id": parent_id,
                "name": parent_name,
                "color": color,
                "icon": icon,
                "total": ZERO,
                "count": 0,
                "children": [],
            }
        amount = money(row["total"])
        grouped[parent_id]["total"] += amount
        grouped[parent_id]["count"] += row["count"]
        if row["category__parent_id"]:
            grouped[parent_id]["children"].append(
                {
                    "id": row["category_id"],
                    "name": row["category__name"],
                    "total": amount,
                    "count": row["count"],
                }
            )
    items = sorted(grouped.values(), key=lambda item: item["total"], reverse=True)
    for item in items:
        item["total"] = money(item["total"])
    return items


def _serialize_tx(tx: Transaction) -> dict:
    return {
        "id": tx.id,
        "amount": str(money(tx.amount)),
        "transaction_type": tx.transaction_type,
        "merchant": tx.merchant,
        "description": tx.description,
        "transaction_date": tx.transaction_date.isoformat(),
        "account": tx.account_id,
        "account_name": tx.account.name,
        "category": tx.category_id,
        "category_name": tx.category.name if tx.category_id else None,
        "category_icon": tx.category.icon if tx.category_id else "circle",
        "category_color": tx.category.color if tx.category_id else "#6B7280",
        "notes": tx.notes,
        "payment_method": tx.payment_method,
    }


def _budget_progress(user, year: int, month: int, today: date):
    budget = (
        Budget.objects.filter(user=user, year=year, month=month)
        .prefetch_related("items__category")
        .first()
    )
    if not budget:
        return None
    start, end = month_bounds(year, month)
    days_in_month = monthrange(year, month)[1]
    days_elapsed = today.day if (year, month) == (today.year, today.month) else days_in_month
    days_remaining = max(days_in_month - days_elapsed, 0)
    items = []
    for item in budget.items.all():
        cat_ids = [item.category_id]
        cat_ids.extend(item.category.children.values_list("id", flat=True))
        spent = money(
            Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.Type.EXPENSE,
                category_id__in=cat_ids,
                transaction_date__gte=start,
                transaction_date__lte=end,
                status=Transaction.Status.CLEARED,
            ).aggregate(t=Sum("amount"))["t"]
            or ZERO
        )
        allocated = money(item.allocated_amount)
        remaining = money(allocated - spent)
        used_pct = percent(spent, allocated)
        daily_avg = money(spent / days_elapsed) if days_elapsed else ZERO
        projected = money(daily_avg * days_in_month)
        required_daily = money(remaining / days_remaining) if days_remaining and remaining > ZERO else ZERO
        items.append(
            {
                "id": item.id,
                "category": item.category_id,
                "category_name": item.category.name,
                "category_icon": item.category.icon,
                "category_color": item.category.color,
                "allocated": allocated,
                "spent": spent,
                "remaining": remaining,
                "used_percent": used_pct,
                "days_remaining": days_remaining,
                "projected": projected,
                "required_daily": required_daily,
                "insight": _budget_insight(item.category.name, remaining, days_remaining, projected, allocated),
            }
        )
    return {"id": budget.id, "name": budget.name, "items": items, "days_remaining": days_remaining}


def _budget_insight(name, remaining, days_remaining, projected, allocated):
    remaining = money(remaining)
    if remaining <= ZERO:
        return f"The {name.lower()} budget is fully used."
    if projected > allocated:
        return f"At this pace, {name.lower()} spending may exceed this month's budget."
    return f"You have Rs. {remaining:,.0f} remaining in your {name.lower()} budget and {days_remaining} days left."


def _upcoming_bills(user, today: date, limit=6):
    bills = (
        Bill.objects.filter(user=user, is_active=True)
        .exclude(status__in=[Bill.Status.PAID, Bill.Status.SKIPPED])
        .filter(due_date__gte=today - timedelta(days=3))
        .select_related("category", "account")
        .order_by("due_date")[:limit]
    )
    payload = []
    for bill in bills:
        status = bill.status
        if bill.due_date < today:
            status = Bill.Status.OVERDUE
        elif (bill.due_date - today).days <= 3:
            status = Bill.Status.DUE_SOON
        payload.append(
            {
                "id": bill.id,
                "name": bill.name,
                "amount": str(money(bill.amount)),
                "due_date": bill.due_date.isoformat(),
                "status": status,
                "category_name": bill.category.name if bill.category_id else None,
            }
        )
    return payload


def build_dashboard(user, year: int | None = None, month: int | None = None) -> dict:
    now = timezone.localtime()
    today = now.date()
    year = year or today.year
    month = month or today.month
    start, end = month_bounds(year, month)
    prev_y, prev_m = _shift_month(year, month, -1)
    prev_start, prev_end = month_bounds(prev_y, prev_m)

    current = _month_totals(user, start, end)
    previous = _month_totals(user, prev_start, prev_end)

    asset_balance = ZERO
    for account in Account.objects.filter(user=user, is_archived=False):
        if account.is_liability:
            continue
        asset_balance += money(account.current_balance)

    prev_expenses = previous["expenses"] or Decimal("1")
    expense_change = percent(current["expenses"] - previous["expenses"], prev_expenses) if previous["expenses"] else ZERO
    balance_change = percent(current["saved"], previous["income"]) if previous["income"] else ZERO

    recent = (
        Transaction.objects.filter(user=user)
        .select_related("account", "category")
        .order_by("-transaction_date", "-id")[:8]
    )
    snapshot_net_worth(user, today)
    net = compute_net_worth(user)
    sts = calculate_safe_to_spend(user, today)
    today_money = daily_allowance(user, today)
    accounts = [
        {
            "id": account.id,
            "name": account.name,
            "balance": money(account.current_balance),
            "color": account.color,
            "account_type": account.account_type,
            "is_liability": account.is_liability,
        }
        for account in Account.objects.filter(user=user, is_archived=False)
    ]

    unread = Notification.objects.filter(user=user, is_read=False).count()
    profile = user.profile
    display = profile.display_name or user.get_full_name() or user.username

    return {
        "greeting": _greeting(now),
        "display_name": display,
        "date": today.isoformat(),
        "year": year,
        "month": month,
        "currency": profile.currency,
        "currency_symbol": profile.currency_symbol,
        "hide_balance": profile.hide_balance,
        "total_balance": asset_balance,
        "balance_change_percent": balance_change,
        "safe_to_spend": sts,
        "month_overview": current,
        "previous_month": previous,
        "expense_change_percent": expense_change,
        "today": today_money,
        "spending_chart": _spending_series(user, year, month),
        "categories": _category_breakdown(user, start, end),
        "recent_transactions": [_serialize_tx(tx) for tx in recent],
        "upcoming_bills": _upcoming_bills(user, today),
        "budgets": _budget_progress(user, year, month, today),
        "goals": [
            {
                "id": goal.id,
                "name": goal.name,
                "target_amount": str(goal.target_amount),
                "current_amount": str(goal.current_amount),
                "color": goal.color,
                "icon": goal.icon,
                "progress": percent(goal.current_amount, goal.target_amount),
            }
            for goal in SavingsGoal.objects.filter(user=user, status=SavingsGoal.Status.ACTIVE)[:4]
        ],
        "accounts": accounts,
        "net_worth": net["net_worth"],
        "net_worth_assets": net["assets"],
        "net_worth_liabilities": net["liabilities"],
        "unread_notifications": unread,
        "subscription_monthly": _subscription_monthly(user),
    }


def _subscription_monthly(user):
    total = ZERO
    for sub in Subscription.objects.filter(user=user, status=Subscription.Status.ACTIVE):
        price = money(sub.price)
        if sub.billing_cycle == "yearly":
            total += money(price / 12)
        elif sub.billing_cycle == "weekly":
            total += money(price * Decimal("4.345"))
        else:
            total += price
    return money(total)


def serialize_decimal(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: serialize_decimal(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_decimal(v) for v in value]
    return value
