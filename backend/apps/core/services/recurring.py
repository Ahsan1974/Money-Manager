from calendar import monthrange
from datetime import date, timedelta

from django.utils import timezone

from apps.bills.models import Bill, Subscription
from apps.core.models import Notification, UserProfile
from apps.core.services.ledger import create_transaction
from apps.core.services.money import money
from apps.transactions.models import Transaction


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def add_period(value: date, frequency: str) -> date:
    if frequency == "weekly":
        return value + timedelta(days=7)
    if frequency == "yearly":
        return add_months(value, 12)
    if frequency == "once":
        return value
    return add_months(value, 1)


def refresh_bill_statuses(user, today: date | None = None):
    today = today or timezone.localdate()
    changed = []
    for bill in Bill.objects.filter(user=user, is_active=True):
        if bill.status in {Bill.Status.PAID, Bill.Status.SKIPPED} and bill.frequency == "once":
            continue
        if bill.status == Bill.Status.PAID and bill.due_date >= today:
            continue
        previous = bill.status
        if bill.due_date < today and bill.status != Bill.Status.PAID:
            bill.status = Bill.Status.OVERDUE
        elif 0 <= (bill.due_date - today).days <= 3 and bill.status != Bill.Status.PAID:
            bill.status = Bill.Status.DUE_SOON
        elif bill.status != Bill.Status.PAID:
            bill.status = Bill.Status.UPCOMING
        if bill.status != previous:
            changed.append(bill)
    if changed:
        Bill.objects.bulk_update(changed, ["status"])


def pay_bill(bill: Bill, paid_on: date | None = None, create_tx: bool = True) -> Bill:
    paid_on = paid_on or timezone.localdate()
    if create_tx and bill.account_id:
        create_transaction(
            user=bill.user,
            account=bill.account,
            amount=bill.amount,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date=paid_on,
            category=bill.category,
            merchant=bill.name,
            description=f"{bill.name} bill",
            payment_method=Transaction.Method.BANK,
        )
    bill.last_paid_on = paid_on
    if bill.frequency == "once":
        bill.status = Bill.Status.PAID
    else:
        bill.due_date = add_period(bill.due_date, bill.frequency)
        bill.status = Bill.Status.UPCOMING
    bill.save()
    return bill


def generate_due_notifications(user, today: date | None = None):
    today = today or timezone.localdate()
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if profile.notify_bills:
        for bill in Bill.objects.filter(user=user, is_active=True).exclude(
            status__in=[Bill.Status.PAID, Bill.Status.SKIPPED]
        ):
            days = (bill.due_date - today).days
            if days in {0, 1, bill.reminder_days}:
                title = f"{bill.name} due {'today' if days == 0 else 'tomorrow' if days == 1 else f'in {days} days'}"
                Notification.objects.get_or_create(
                    user=user,
                    kind=Notification.Kind.BILL,
                    title=title,
                    message=f"{bill.name} of Rs. {money(bill.amount):,.0f} is due on {bill.due_date.isoformat()}.",
                    link="/app/bills",
                )
    if profile.notify_subscriptions:
        soon = today + timedelta(days=3)
        for sub in Subscription.objects.filter(
            user=user,
            status=Subscription.Status.ACTIVE,
            next_billing_date__lte=soon,
            next_billing_date__gte=today,
        ):
            Notification.objects.get_or_create(
                user=user,
                kind=Notification.Kind.SUBSCRIPTION,
                title=f"{sub.name} renews soon",
                message=f"{sub.name} renews on {sub.next_billing_date.isoformat()} for Rs. {money(sub.price):,.0f}.",
                link="/app/subscriptions",
            )
