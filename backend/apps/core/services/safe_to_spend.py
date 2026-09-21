from calendar import monthrange
from datetime import date, timedelta

from django.db.models import Sum

from apps.accounts.models import Account
from apps.bills.models import Bill
from apps.core.models import UserProfile
from apps.core.services.money import ZERO, money
from apps.debts.models import Debt
from apps.goals.models import SavingsGoal
from apps.transactions.models import Transaction


def _profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def available_cash(user):
    total = ZERO
    accounts = Account.objects.filter(
        user=user, is_archived=False, include_in_safe_to_spend=True
    )
    for account in accounts:
        if account.is_liability:
            continue
        total += money(account.current_balance)
    return money(total)


def upcoming_bills_total(user, today: date, horizon_days: int):
    until = today + timedelta(days=horizon_days)
    bills = Bill.objects.filter(
        user=user,
        is_active=True,
        due_date__gte=today,
        due_date__lte=until,
    ).exclude(status__in=[Bill.Status.PAID, Bill.Status.SKIPPED])
    return money(bills.aggregate(total=Sum("amount"))["total"] or ZERO), bills


def upcoming_debt_payments_total(user, today: date, horizon_days: int):
    until = today + timedelta(days=horizon_days)
    total = ZERO
    items = []
    for debt in Debt.objects.filter(user=user, is_active=True):
        payment = money(debt.monthly_payment)
        if payment <= ZERO:
            continue
        if debt.due_day:
            year, month = today.year, today.month
            last = monthrange(year, month)[1]
            due = date(year, month, min(debt.due_day, last))
            if due < today:
                if month == 12:
                    year, month = year + 1, 1
                else:
                    month += 1
                last = monthrange(year, month)[1]
                due = date(year, month, min(debt.due_day, last))
            if today <= due <= until:
                amount = min(payment, money(debt.remaining_amount))
                total += amount
                items.append(debt)
        else:
            amount = min(payment, money(debt.remaining_amount))
            total += amount
            items.append(debt)
    return money(total), items


def reserved_goals_total(user):
    total = ZERO
    goals = SavingsGoal.objects.filter(
        user=user, status=SavingsGoal.Status.ACTIVE, is_reserved=True
    )
    for goal in goals:
        remaining = money(goal.target_amount) - money(goal.current_amount)
        if remaining > ZERO:
            total += remaining
    return money(total), goals


def daily_allowance(user, today: date | None = None):
    today = today or date.today()
    profile = _profile(user)
    sts = calculate_safe_to_spend(user, today)
    days = max(int(profile.daily_spending_period_days or 1), 1)
    remaining_days = days
    # Prefer remaining days in the current month when the period is monthly.
    if profile.daily_spending_period_days == 30:
        last = monthrange(today.year, today.month)[1]
        remaining_days = max(last - today.day + 1, 1)
    spent_today = (
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date=today,
            status=Transaction.Status.CLEARED,
        ).aggregate(total=Sum("amount"))["total"]
        or ZERO
    )
    income_today = (
        Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.INCOME,
            transaction_date=today,
            status=Transaction.Status.CLEARED,
        ).aggregate(total=Sum("amount"))["total"]
        or ZERO
    )
    per_day = money(sts["safe_to_spend"] / remaining_days) if remaining_days else ZERO
    remaining = money(per_day - money(spent_today))
    return {
        "spent_today": money(spent_today),
        "income_today": money(income_today),
        "remaining_daily_allowance": remaining,
        "daily_allowance": per_day,
        "days_in_period": remaining_days,
    }


def calculate_safe_to_spend(user, today: date | None = None) -> dict:
    today = today or date.today()
    profile = _profile(user)
    available = available_cash(user)
    bills_total, bills = (
        upcoming_bills_total(user, today, profile.obligation_horizon_days)
        if profile.include_upcoming_bills
        else (ZERO, Bill.objects.none())
    )
    debts_total, debts = (
        upcoming_debt_payments_total(user, today, profile.obligation_horizon_days)
        if profile.include_debt_payments
        else (ZERO, [])
    )
    goals_total, goals = (
        reserved_goals_total(user) if profile.include_goal_reserves else (ZERO, SavingsGoal.objects.none())
    )
    emergency = money(profile.emergency_reserve)
    savings_reserve = money(profile.savings_reserve)
    safe = money(
        available - bills_total - debts_total - goals_total - emergency - savings_reserve
    )
    return {
        "available": available,
        "upcoming_bills": bills_total,
        "debt_payments": debts_total,
        "goal_reserve": goals_total,
        "emergency_reserve": emergency,
        "savings_reserve": savings_reserve,
        "safe_to_spend": safe,
        "horizon_days": profile.obligation_horizon_days,
        "bill_count": bills.count() if hasattr(bills, "count") else len(list(bills)),
        "debt_count": len(list(debts)),
        "goal_count": goals.count() if hasattr(goals, "count") else len(list(goals)),
    }
