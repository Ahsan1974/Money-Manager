import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from apps.accounts.models import Account
from apps.core.services.money import money
from apps.transactions.models import Category, Transaction

CATEGORY_KEYWORDS = {
    "Food": [
        "lunch", "dinner", "breakfast", "brunch", "chai", "coffee", "grocery",
        "groceries", "food", "restaurant", "pizza", "biryani", "burger", "snack",
        "cafe", "tea", "dine", "eating",
    ],
    "Transport": [
        "fuel", "petrol", "diesel", "careem", "uber", "indrive", "parking",
        "metro", "bus", "taxi", "transport", "ride",
    ],
    "Bills": [
        "electricity", "internet", "gas", "water", "wifi", "bill", "k-electric",
        "ptcl", "ssgc",
    ],
    "Shopping": ["shopping", "clothes", "amazon", "daraz", "mall", "store"],
    "Entertainment": ["netflix", "movie", "cinema", "game", "spotify", "concert"],
    "Health": ["pharmacy", "medicine", "doctor", "hospital", "clinic", "gym"],
    "Education": ["course", "book", "tuition", "university", "fee", "thesis"],
    "Travel": ["hotel", "flight", "ticket", "airbnb", "travel"],
    "Subscriptions": ["subscription", "chatgpt", "github", "icloud", "google one"],
    "Salary": ["salary", "payroll", "wage"],
}

INCOME_HINTS = [
    "received", "got", "salary", "income", "paid me", "from", "freelance", "refund",
]
EXPENSE_HINTS = ["paid", "spent", "bought", "bill", "for"]


def _find_category(user, text: str, tx_type: str):
    lowered = text.lower()
    wanted_kind = Category.Kind.INCOME if tx_type == Transaction.Type.INCOME else Category.Kind.EXPENSE
    for name, keywords in CATEGORY_KEYWORDS.items():
        if any(word in lowered for word in keywords):
            cat = Category.objects.filter(user=user, name__iexact=name).first()
            if cat:
                return cat
    fallback_name = "Salary" if wanted_kind == Category.Kind.INCOME else "Other"
    return Category.objects.filter(user=user, name__iexact=fallback_name).first()


def _find_account(user, text: str):
    lowered = text.lower()
    for account in Account.objects.filter(user=user, is_archived=False):
        if account.name.lower() in lowered or (account.institution and account.institution.lower() in lowered):
            return account
    cash = Account.objects.filter(user=user, account_type=Account.Type.CASH, is_archived=False).first()
    if cash:
        return cash
    return Account.objects.filter(user=user, is_archived=False).first()


def parse_natural_language(user, text: str, today: date | None = None) -> dict:
    today = today or date.today()
    original = text.strip()
    if not original:
        return {"ok": False, "error": "Please enter something like “450 lunch”."}

    lowered = original.lower()
    amount = None
    match = re.search(r"(?:rs\.?|pkr)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)", lowered)
    if match:
        raw = match.group(1).replace(",", "")
        try:
            amount = money(raw)
        except (InvalidOperation, ValueError):
            amount = None
    if amount is None or amount <= 0:
        return {"ok": False, "error": "I could not find a valid amount. Try “450 lunch”."}

    tx_type = Transaction.Type.EXPENSE
    if any(hint in lowered for hint in INCOME_HINTS) and not any(
        word in lowered for word in ["bill", "paid for", "spent"]
    ):
        tx_type = Transaction.Type.INCOME
    if "received" in lowered or "salary" in lowered:
        tx_type = Transaction.Type.INCOME

    tx_date = today
    if "yesterday" in lowered:
        tx_date = today - timedelta(days=1)
    elif "today" in lowered:
        tx_date = today

    remainder = original
    remainder = re.sub(r"(?i)(rs\.?|pkr)\s*", "", remainder)
    remainder = re.sub(r"[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?", "", remainder, count=1)
    remainder = re.sub(r"(?i)\b(today|yesterday|received|got|paid|spent|bought)\b", "", remainder)
    description = " ".join(remainder.split()).strip(" -–") or original

    category = _find_category(user, lowered, tx_type)
    account = _find_account(user, lowered)
    merchant = description[:160]
    ambiguous = False
    confidence = "high"
    if not category or description.lower() in {"", "from"}:
        ambiguous = True
        confidence = "low"
    if len(description) < 3:
        ambiguous = True
        confidence = "low"

    return {
        "ok": True,
        "ambiguous": ambiguous,
        "confidence": confidence,
        "draft": {
            "amount": str(amount),
            "transaction_type": tx_type,
            "description": description,
            "merchant": merchant,
            "category": category.id if category else None,
            "category_name": category.name if category else None,
            "account": account.id if account else None,
            "account_name": account.name if account else None,
            "transaction_date": tx_date.isoformat(),
            "notes": "",
            "source_text": original,
        },
    }
