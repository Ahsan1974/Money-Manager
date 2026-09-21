from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from apps.bills.models import Bill, Subscription
from apps.core.services.ledger import month_bounds
from apps.core.services.money import ZERO, money, percent
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


def generate_insights(user, today: date | None = None) -> list[dict]:
    today = today or date.today()
    start, end = month_bounds(today.year, today.month)
    prev_y, prev_m = _shift_month(today.year, today.month, -1)
    prev_start, prev_end = month_bounds(prev_y, prev_m)
    insights: list[dict] = []

    def spent(category_name: str, range_start, range_end):
        return money(
            Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.Type.EXPENSE,
                transaction_date__gte=range_start,
                transaction_date__lte=range_end,
                status=Transaction.Status.CLEARED,
            )
            .filter(category__name__iexact=category_name)
            .aggregate(t=Sum("amount"))["t"]
            or ZERO
        )

    def spent_tree(name, range_start, range_end):
        qs = Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__gte=range_start,
            transaction_date__lte=range_end,
            status=Transaction.Status.CLEARED,
        ).filter(category__name__iexact=name) | Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__gte=range_start,
            transaction_date__lte=range_end,
            status=Transaction.Status.CLEARED,
            category__parent__name__iexact=name,
        )
        return money(qs.aggregate(t=Sum("amount"))["t"] or ZERO)

    for name in ["Food", "Transport", "Shopping", "Entertainment", "Bills"]:
        current = spent_tree(name, start, end)
        previous = spent_tree(name, prev_start, prev_end)
        if previous > ZERO and current > previous:
            diff = money(current - previous)
            insights.append(
                {
                    "id": f"up-{name.lower()}",
                    "tone": "warning",
                    "title": f"{name} spending increased",
                    "body": f"Your {name.lower()} spending increased compared with last month by Rs. {diff:,.0f}.",
                }
            )
        elif previous > ZERO and current < previous * Decimal("0.85"):
            insights.append(
                {
                    "id": f"down-{name.lower()}",
                    "tone": "success",
                    "title": f"{name} spending slowed",
                    "body": f"You spent less on {name.lower()} this month than last month.",
                }
            )

    week_end = today + timedelta(days=7)
    due_soon = Bill.objects.filter(
        user=user,
        is_active=True,
        due_date__gte=today,
        due_date__lte=week_end,
    ).exclude(status__in=[Bill.Status.PAID, Bill.Status.SKIPPED])
    count = due_soon.count()
    if count:
        insights.append(
            {
                "id": "bills-week",
                "tone": "info",
                "title": "Bills due this week",
                "body": f"You have {count} bill{'s' if count != 1 else ''} due within the next 7 days.",
            }
        )

    income = money(
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.INCOME,
            transaction_date__gte=start,
            transaction_date__lte=end,
            status=Transaction.Status.CLEARED,
        ).aggregate(t=Sum("amount"))["t"]
        or ZERO
    )
    expenses = money(
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__gte=start,
            transaction_date__lte=end,
            status=Transaction.Status.CLEARED,
        ).aggregate(t=Sum("amount"))["t"]
        or ZERO
    )
    saved = money(income - expenses)
    prev_income = money(
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.INCOME,
            transaction_date__gte=prev_start,
            transaction_date__lte=prev_end,
            status=Transaction.Status.CLEARED,
        ).aggregate(t=Sum("amount"))["t"]
        or ZERO
    )
    prev_saved = money(
        prev_income
        - money(
            Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.Type.EXPENSE,
                transaction_date__gte=prev_start,
                transaction_date__lte=prev_end,
                status=Transaction.Status.CLEARED,
            ).aggregate(t=Sum("amount"))["t"]
            or ZERO
        )
    )
    if saved > prev_saved and income > ZERO:
        insights.append(
            {
                "id": "saved-up",
                "tone": "success",
                "title": "Savings contribution increased",
                "body": "Your savings contribution increased this month compared with last month.",
            }
        )

    sub_month = ZERO
    for sub in Subscription.objects.filter(user=user, status=Subscription.Status.ACTIVE):
        price = money(sub.price)
        if sub.billing_cycle == "yearly":
            sub_month += money(price / 12)
        elif sub.billing_cycle == "weekly":
            sub_month += money(price * Decimal("4.345"))
        else:
            sub_month += price
    if expenses > ZERO and sub_month > ZERO:
        share = percent(sub_month, expenses)
        insights.append(
            {
                "id": "subs-share",
                "tone": "info",
                "title": "Subscriptions",
                "body": f"Your subscription expenses represent {share}% of this month's expenses so far.",
            }
        )

    days_elapsed = max(today.day, 1)
    days_in_month = monthrange(today.year, today.month)[1]
    if days_elapsed >= 5 and expenses > ZERO:
        projected = money(expenses / days_elapsed * days_in_month)
        if income > ZERO and projected > income:
            insights.append(
                {
                    "id": "overspend-pace",
                    "tone": "warning",
                    "title": "Spending pace",
                    "body": "Your current spending rate may exceed this month's income if it continues.",
                }
            )

    if not insights:
        insights.append(
            {
                "id": "quiet",
                "tone": "info",
                "title": "All quiet",
                "body": "There are no notable changes to highlight yet. Keep logging transactions.",
            }
        )
    return insights[:8]
