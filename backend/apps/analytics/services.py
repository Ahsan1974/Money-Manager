from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Count, Max, Min, Sum

from apps.analytics.models import NetWorthSnapshot
from apps.bills.models import Subscription
from apps.budgets.models import Budget
from apps.core.services.dashboard import _budget_progress, _category_breakdown, _month_totals
from apps.core.services.ledger import month_bounds
from apps.core.services.money import ZERO, money, percent, savings_rate
from apps.core.services.networth import compute_net_worth
from apps.transactions.models import Transaction


def _shift_month(year, month, delta):
    month += delta
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return year, month


def analytics_overview(user, year: int, month: int) -> dict:
    start, end = month_bounds(year, month)
    totals = _month_totals(user, start, end)
    days = monthrange(year, month)[1]
    today = date.today()
    elapsed = today.day if (year, month) == (today.year, today.month) else days

    expenses = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.Type.EXPENSE,
        transaction_date__gte=start,
        transaction_date__lte=end,
        status=Transaction.Status.CLEARED,
    )
    largest = expenses.order_by("-amount").select_related("category", "account").first()
    by_day = (
        expenses.values("transaction_date").annotate(total=Sum("amount")).order_by("-total").first()
    )
    merchants = list(
        expenses.exclude(merchant="")
        .values("merchant")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")[:8]
    )
    for row in merchants:
        row["total"] = money(row["total"])

    income_trend = []
    expense_trend = []
    savings_trend = []
    for offset in range(11, -1, -1):
        y, m = _shift_month(year, month, -offset)
        s, e = month_bounds(y, m)
        t = _month_totals(user, s, e)
        label = date(y, m, 1).strftime("%b %Y")
        income_trend.append({"label": label, "amount": t["income"]})
        expense_trend.append({"label": label, "amount": t["expenses"]})
        savings_trend.append({"label": label, "amount": t["saved"]})

    snapshots = list(
        NetWorthSnapshot.objects.filter(user=user).order_by("snapshot_date").values(
            "snapshot_date", "assets", "liabilities", "net_worth"
        )
    )
    net = compute_net_worth(user)
    subs_month = ZERO
    largest_sub = None
    active_subs = Subscription.objects.filter(user=user, status=Subscription.Status.ACTIVE)
    for sub in active_subs:
        price = money(sub.price)
        monthly = price
        if sub.billing_cycle == "yearly":
            monthly = money(price / 12)
        elif sub.billing_cycle == "weekly":
            monthly = money(price * Decimal("4.345"))
        subs_month += monthly
        if largest_sub is None or price > money(largest_sub.price):
            largest_sub = sub

    return {
        "year": year,
        "month": month,
        "income": totals["income"],
        "expenses": totals["expenses"],
        "saved": totals["saved"],
        "savings_rate": totals["savings_rate"],
        "daily_average": money(totals["expenses"] / elapsed) if elapsed else ZERO,
        "monthly_average": money(sum(p["amount"] for p in expense_trend[-6:]) / 6) if expense_trend else ZERO,
        "highest_spending_day": {
            "date": by_day["transaction_date"].isoformat() if by_day else None,
            "amount": money(by_day["total"]) if by_day else ZERO,
        },
        "largest_transaction": {
            "id": largest.id if largest else None,
            "amount": money(largest.amount) if largest else ZERO,
            "merchant": largest.merchant if largest else None,
            "date": largest.transaction_date.isoformat() if largest else None,
            "category": largest.category.name if largest and largest.category_id else None,
        },
        "top_merchants": merchants,
        "categories": _category_breakdown(user, start, end),
        "income_trend": income_trend,
        "expense_trend": expense_trend,
        "savings_trend": savings_trend,
        "budgets": _budget_progress(user, year, month, today),
        "net_worth": net,
        "net_worth_history": [
            {
                "date": row["snapshot_date"].isoformat(),
                "assets": money(row["assets"]),
                "liabilities": money(row["liabilities"]),
                "net_worth": money(row["net_worth"]),
            }
            for row in snapshots
        ],
        "subscriptions": {
            "monthly": money(subs_month),
            "annual": money(subs_month * 12),
            "active": active_subs.count(),
            "largest": largest_sub.name if largest_sub else None,
            "largest_amount": money(largest_sub.price) if largest_sub else ZERO,
        },
    }


def yearly_review(user, year: int) -> dict:
    start, end = date(year, 1, 1), date(year, 12, 31)
    totals = _month_totals(user, start, end)
    months_elapsed = date.today().month if year == date.today().year else 12
    categories = _category_breakdown(user, start, end)
    largest_cat = categories[0] if categories else None
    largest_tx = (
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__year=year,
            status=Transaction.Status.CLEARED,
        )
        .order_by("-amount")
        .select_related("category")
        .first()
    )
    snapshots = list(
        NetWorthSnapshot.objects.filter(user=user, snapshot_date__year=year).order_by("snapshot_date")
    )
    nw_change = ZERO
    if snapshots:
        nw_change = money(snapshots[-1].net_worth) - money(snapshots[0].net_worth)
    monthly = []
    for month in range(1, 13):
        s, e = month_bounds(year, month)
        monthly.append({"month": month, **_month_totals(user, s, e)})
    return {
        "year": year,
        "total_income": totals["income"],
        "total_expenses": totals["expenses"],
        "total_saved": totals["saved"],
        "savings_rate": totals["savings_rate"],
        "average_monthly_income": money(totals["income"] / months_elapsed) if months_elapsed else ZERO,
        "average_monthly_expenses": money(totals["expenses"] / months_elapsed) if months_elapsed else ZERO,
        "largest_category": largest_cat["name"] if largest_cat else None,
        "largest_category_amount": largest_cat["total"] if largest_cat else ZERO,
        "largest_expense": largest_tx.merchant or largest_tx.description if largest_tx else None,
        "largest_expense_amount": money(largest_tx.amount) if largest_tx else ZERO,
        "net_worth_change": nw_change,
        "categories": categories,
        "monthly": monthly,
        "title": f"{year} Financial Summary",
    }


def health_indicators(user, year: int, month: int) -> dict:
    start, end = month_bounds(year, month)
    totals = _month_totals(user, start, end)
    prev_y, prev_m = _shift_month(year, month, -1)
    prev = _month_totals(user, *month_bounds(prev_y, prev_m))
    net = compute_net_worth(user)
    expense_growth = percent(totals["expenses"] - prev["expenses"], prev["expenses"] or Decimal("1"))
    from apps.core.services.dashboard import _subscription_monthly

    recurring = _subscription_monthly(user)
    recurring_ratio = percent(recurring, totals["expenses"]) if totals["expenses"] else ZERO
    debt_ratio = percent(net["liabilities"], net["assets"]) if net["assets"] else ZERO
    budget = _budget_progress(user, year, month, date.today())
    adherence = ZERO
    if budget and budget["items"]:
        hits = sum(1 for item in budget["items"] if item["spent"] <= item["allocated"])
        adherence = percent(hits, len(budget["items"]))
    from apps.core.models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=user)
    emergency_progress = (
        percent(min(net["assets"], profile.emergency_reserve), profile.emergency_reserve)
        if profile.emergency_reserve
        else ZERO
    )
    return {
        "savings_rate": totals["savings_rate"],
        "expense_growth": expense_growth,
        "budget_adherence": adherence,
        "emergency_reserve_progress": emergency_progress,
        "debt_ratio": debt_ratio,
        "recurring_expense_ratio": recurring_ratio,
        "methodology": {
            "savings_rate": "Income minus expenses, divided by income, for the selected month. Transfers are excluded.",
            "expense_growth": "This month's expenses compared with the previous month.",
            "budget_adherence": "Share of budget categories that are within their allocation so far.",
            "emergency_reserve_progress": "Assets versus the emergency reserve you configured in Settings.",
            "debt_ratio": "Liabilities divided by assets.",
            "recurring_expense_ratio": "Active subscriptions (monthly equivalent) divided by this month's expenses.",
        },
    }
