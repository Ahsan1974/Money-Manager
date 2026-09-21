from decimal import Decimal, ROUND_HALF_EVEN

from apps.core.services.money import ZERO, money


def savings_projection(monthly_contribution, months, annual_rate_pct=0):
    contrib = money(monthly_contribution)
    n = int(months)
    r = Decimal(str(annual_rate_pct or 0)) / Decimal("100") / Decimal("12")
    if n <= 0:
        return {"future_value": ZERO, "contributed": ZERO, "interest": ZERO}
    if r == 0:
        total = money(contrib * n)
        return {"future_value": total, "contributed": total, "interest": ZERO}
    factor = ((1 + r) ** n - 1) / r
    fv = money(contrib * factor)
    contributed = money(contrib * n)
    return {"future_value": fv, "contributed": contributed, "interest": money(fv - contributed)}


def budget_split(income, allocations: dict):
    income_m = money(income)
    rows = []
    used = ZERO
    for name, pct in allocations.items():
        amount = money(income_m * Decimal(str(pct)) / Decimal("100"))
        used += amount
        rows.append({"name": name, "percent": pct, "amount": amount})
    return {"income": income_m, "items": rows, "unallocated": money(income_m - used)}


def loan_payment(principal, annual_rate_pct, months):
    principal_m = money(principal)
    n = int(months)
    if n <= 0:
        return {"payment": ZERO, "total_paid": ZERO, "total_interest": ZERO}
    r = Decimal(str(annual_rate_pct or 0)) / Decimal("100") / Decimal("12")
    if r == 0:
        payment = money(principal_m / n)
    else:
        one_plus = (Decimal("1") + r) ** n
        payment = money(principal_m * r * one_plus / (one_plus - 1))
    total_paid = money(payment * n)
    return {
        "payment": payment,
        "total_paid": total_paid,
        "total_interest": money(total_paid - principal_m),
        "months": n,
    }


def debt_payoff(balance, annual_rate_pct, monthly_payment):
    bal = money(balance)
    payment = money(monthly_payment)
    r = Decimal(str(annual_rate_pct or 0)) / Decimal("100") / Decimal("12")
    if payment <= ZERO:
        return {"error": "Please enter a monthly payment."}
    months = 0
    interest_paid = ZERO
    current = bal
    # Guardrail for personal-use calculators.
    while current > ZERO and months < 600:
        interest = money(current * r)
        interest_paid += interest
        current = money(current + interest - payment)
        months += 1
        if payment <= interest and r > 0:
            return {
                "error": "This payment does not cover monthly interest.",
                "payment": payment,
            }
    return {
        "months": months,
        "years": money(Decimal(months) / Decimal("12")).quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN),
        "interest_paid": money(interest_paid),
        "total_paid": money(bal + interest_paid),
    }


def percentage_of(part, whole):
    whole_m = money(whole)
    if whole_m == ZERO:
        return {"percent": ZERO}
    return {"percent": money(money(part) * Decimal("100") / whole_m)}


def convert_currency(amount, rate):
    return {"converted": money(money(amount) * Decimal(str(rate)))}
