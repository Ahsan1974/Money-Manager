from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

TWOPLACES = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Any) -> Decimal:
    """Quantize any numeric input to a two-decimal Decimal. Never use float math."""
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        amount = value
    else:
        amount = Decimal(str(value))
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)


def money_sum(values) -> Decimal:
    total = ZERO
    for value in values:
        total += money(value)
    return money(total)


def percent(part: Any, whole: Any) -> Decimal:
    whole_m = money(whole)
    if whole_m == ZERO:
        return ZERO
    return (money(part) * Decimal("100") / whole_m).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_EVEN
    )


def savings_rate(income: Any, expenses: Any) -> Decimal:
    income_m = money(income)
    if income_m <= ZERO:
        return ZERO
    saved = income_m - money(expenses)
    return percent(saved, income_m)
