from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.ai.models import AIConversation, AIMessage
from apps.bills.models import Bill, Subscription
from apps.core.services.dashboard import _category_breakdown, _month_totals, serialize_decimal
from apps.core.services.ledger import create_transaction, month_bounds
from apps.core.services.money import ZERO, money
from apps.core.services.nl import parse_natural_language
from apps.debts.models import LendingRecord
from apps.transactions.models import Category, Transaction


def _current_month():
    today = timezone.localdate()
    return today.year, today.month, today


def finance_tools(user):
    year, month, today = _current_month()
    start, end = month_bounds(year, month)

    def spending(category: str | None = None, year_=year, month_=month):
        s, e = month_bounds(year_, month_)
        qs = Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.Type.EXPENSE,
            transaction_date__gte=s,
            transaction_date__lte=e,
            status=Transaction.Status.CLEARED,
        )
        if category:
            qs = qs.filter(category__name__iexact=category) | Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.Type.EXPENSE,
                transaction_date__gte=s,
                transaction_date__lte=e,
                status=Transaction.Status.CLEARED,
                category__parent__name__iexact=category,
            )
        total = money(qs.aggregate(t=Sum("amount"))["t"] or ZERO)
        children = []
        if category:
            breakdown = _category_breakdown(user, s, e)
            for item in breakdown:
                if item["name"].lower() == category.lower():
                    children = item.get("children") or []
                    total = item["total"]
        return {"total": total, "category": category, "year": year_, "month": month_, "children": children}

    def biggest_expenses(limit=5):
        qs = (
            Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.Type.EXPENSE,
                transaction_date__gte=start,
                transaction_date__lte=end,
                status=Transaction.Status.CLEARED,
            )
            .select_related("category")
            .order_by("-amount")[:limit]
        )
        return [
            {
                "id": tx.id,
                "amount": money(tx.amount),
                "merchant": tx.merchant or tx.description,
                "date": tx.transaction_date.isoformat(),
                "category": tx.category.name if tx.category_id else None,
            }
            for tx in qs
        ]

    def compare_months(a: tuple[int, int], b: tuple[int, int]):
        ta = _month_totals(user, *month_bounds(*a))
        tb = _month_totals(user, *month_bounds(*b))
        return {"first": {"year": a[0], "month": a[1], **ta}, "second": {"year": b[0], "month": b[1], **tb}}

    def saved(year_=None):
        if year_:
            return _month_totals(user, date(year_, 1, 1), date(year_, 12, 31))
        return _month_totals(user, start, end)

    def subscriptions():
        rows = []
        monthly = ZERO
        for sub in Subscription.objects.filter(user=user, status=Subscription.Status.ACTIVE):
            price = money(sub.price)
            m = price
            if sub.billing_cycle == "yearly":
                m = money(price / 12)
            elif sub.billing_cycle == "weekly":
                m = money(price * Decimal("4.345"))
            monthly += m
            rows.append(
                {
                    "name": sub.name,
                    "price": price,
                    "cycle": sub.billing_cycle,
                    "next": sub.next_billing_date.isoformat(),
                }
            )
        return {"items": rows, "monthly": money(monthly)}

    def lending():
        lent = ZERO
        borrowed = ZERO
        people = []
        for rec in LendingRecord.objects.filter(user=user).select_related("person"):
            remaining = money(rec.remaining_amount)
            if rec.direction == LendingRecord.Direction.LENT:
                lent += remaining
            else:
                borrowed += remaining
            people.append(
                {
                    "person": rec.person.name,
                    "direction": rec.direction,
                    "remaining": remaining,
                    "status": rec.status,
                }
            )
        return {"owed_to_me": money(lent), "i_owe": money(borrowed), "records": people}

    def bills():
        items = [
            {
                "name": bill.name,
                "amount": money(bill.amount),
                "due": bill.due_date.isoformat(),
                "status": bill.status,
            }
            for bill in Bill.objects.filter(user=user, is_active=True).order_by("due_date")[:12]
        ]
        return {"items": items}

    return {
        "spending": spending,
        "biggest_expenses": biggest_expenses,
        "compare_months": compare_months,
        "saved": saved,
        "subscriptions": subscriptions,
        "lending": lending,
        "bills": bills,
        "totals": lambda: _month_totals(user, start, end),
    }


MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _extract_months(text: str, default_year: int):
    found = []
    lowered = text.lower()
    for name, num in MONTHS.items():
        if name in lowered:
            found.append((default_year, num))
    return found


def answer_locally(user, message: str) -> dict:
    text = message.strip()
    lowered = text.lower()
    tools = finance_tools(user)
    year, month, today = _current_month()
    actions = []

    if lowered.startswith("add ") or "add a" in lowered or "expense" in lowered and any(ch.isdigit() for ch in lowered):
        parsed = parse_natural_language(user, text, today)
        if parsed.get("ok"):
            return {
                "reply": "I prepared this transaction. Confirm to save it — nothing has been recorded yet.",
                "draft": parsed["draft"],
                "needs_confirmation": True,
                "source": "local",
            }

    if "subscription" in lowered:
        data = tools["subscriptions"]()
        lines = [f"{row['name']}: Rs. {row['price']:,.0f} / {row['cycle']}" for row in data["items"]]
        body = "You have no active subscriptions." if not lines else "\n".join(lines)
        return {
            "reply": f"You spend approximately Rs. {data['monthly']:,.0f}/month on recurring subscriptions.\n\n{body}",
            "data": serialize_decimal(data),
            "source": "local",
        }

    if "owe" in lowered or "lent" in lowered or "borrow" in lowered:
        data = tools["lending"]()
        return {
            "reply": (
                f"People owe you Rs. {data['owed_to_me']:,.0f}. "
                f"You owe others Rs. {data['i_owe']:,.0f}."
            ),
            "data": serialize_decimal(data),
            "source": "local",
        }

    if "bill" in lowered:
        data = tools["bills"]()
        lines = [f"{row['name']} — Rs. {row['amount']:,.0f} on {row['due']} ({row['status']})" for row in data["items"]]
        return {"reply": "Upcoming bills:\n" + ("\n".join(lines) or "None"), "data": data, "source": "local"}

    if "compare" in lowered:
        months = _extract_months(lowered, year)
        if len(months) >= 2:
            data = tools["compare_months"](months[0], months[1])
            a, b = data["first"], data["second"]
            return {
                "reply": (
                    f"{a['month']}/{a['year']}: income Rs. {a['income']:,.0f}, expenses Rs. {a['expenses']:,.0f}, saved Rs. {a['saved']:,.0f}.\n"
                    f"{b['month']}/{b['year']}: income Rs. {b['income']:,.0f}, expenses Rs. {b['expenses']:,.0f}, saved Rs. {b['saved']:,.0f}."
                ),
                "data": serialize_decimal(data),
                "source": "local",
            }

    if "save" in lowered or "saved" in lowered:
        scope_year = year if "year" in lowered else None
        data = tools["saved"](scope_year)
        label = f"{year}" if scope_year else "this month"
        return {
            "reply": f"You saved Rs. {data['saved']:,.0f} in {label} (savings rate {data['savings_rate']}%).",
            "data": serialize_decimal(data),
            "source": "local",
        }

    if "biggest" in lowered or "largest" in lowered:
        rows = tools["biggest_expenses"]()
        if not rows:
            return {"reply": "There are no expenses recorded for this month.", "source": "local"}
        lines = [f"Rs. {row['amount']:,.0f} — {row['merchant']} ({row['date']})" for row in rows]
        return {"reply": "Your biggest expenses this month:\n" + "\n".join(lines), "source": "local"}

    category = None
    for name in [
        "food", "transport", "shopping", "entertainment", "health", "education",
        "travel", "bills", "subscriptions", "fuel", "groceries",
    ]:
        if name in lowered:
            category = name.title() if name != "bills" else "Bills"
            break
    if "spend" in lowered or category:
        data = tools["spending"](category)
        if data["total"] == ZERO:
            label = category or "all categories"
            return {
                "reply": f"I don't have spending recorded for {label} this month.",
                "source": "local",
            }
        extra = ""
        if data["children"]:
            extra = "\n" + "\n".join(
                f"{child['name']}: Rs. {money(child['total']):,.0f}" for child in data["children"]
            )
        label = category or "all categories"
        return {
            "reply": f"You spent Rs. {data['total']:,.0f} on {label} in {date(year, month, 1).strftime('%B')}.{extra}",
            "data": serialize_decimal(data),
            "source": "local",
        }

    totals = tools["totals"]()
    return {
        "reply": (
            f"This month you earned Rs. {totals['income']:,.0f}, "
            f"spent Rs. {totals['expenses']:,.0f}, and saved Rs. {totals['saved']:,.0f}."
        ),
        "data": serialize_decimal(totals),
        "source": "local",
    }


def confirm_draft_transaction(user, draft: dict) -> Transaction:
    from apps.accounts.models import Account

    account = Account.objects.get(user=user, pk=draft["account"])
    category = None
    if draft.get("category"):
        category = Category.objects.filter(user=user, pk=draft["category"]).first()
    return create_transaction(
        user=user,
        account=account,
        amount=draft["amount"],
        transaction_type=draft["transaction_type"],
        transaction_date=draft["transaction_date"],
        category=category,
        merchant=draft.get("merchant") or "",
        description=draft.get("description") or "",
        notes=draft.get("notes") or "",
    )


def chat(user, message: str, conversation: AIConversation | None = None) -> dict:
    if conversation is None:
        conversation = AIConversation.objects.create(user=user, title=message[:80])
    AIMessage.objects.create(conversation=conversation, role=AIMessage.Role.USER, content=message)
    from django.conf import settings

    from apps.ai.groq import answer_with_groq

    result = None
    if (settings.AI_API_KEY or "").strip():
        try:
            result = answer_with_groq(user, message)
        except Exception:
            result = None
    if not result:
        result = answer_locally(user, message)
        result["source"] = result.get("source") or "local"
    AIMessage.objects.create(
        conversation=conversation,
        role=AIMessage.Role.ASSISTANT,
        content=result["reply"],
        metadata={k: v for k, v in result.items() if k != "reply"},
    )
    conversation.title = conversation.title or message[:80]
    conversation.save(update_fields=["updated_at", "title"])
    result["conversation_id"] = conversation.id
    return result
