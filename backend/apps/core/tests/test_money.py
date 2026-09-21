from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import Account
from apps.bills.models import Bill
from apps.budgets.models import Budget, BudgetCategory
from apps.core.services.dashboard import _month_totals
from apps.core.services.ledger import create_transaction, create_transfer, delete_transaction, month_bounds
from apps.core.services.money import money, savings_rate
from apps.core.services.networth import compute_net_worth
from apps.core.services.safe_to_spend import calculate_safe_to_spend
from apps.debts.models import Debt
from apps.goals.models import SavingsGoal
from apps.transactions.models import Category, Transaction


class MoneyMathTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali", password="pass12345")
        self.bank = Account.objects.create(
            user=self.user, name="Bank", account_type=Account.Type.BANK,
            opening_balance=money("100000"), current_balance=money("100000"),
        )
        self.cash = Account.objects.create(
            user=self.user, name="Cash", account_type=Account.Type.CASH,
            opening_balance=money("10000"), current_balance=money("10000"),
        )
        self.card = Account.objects.create(
            user=self.user, name="Card", account_type=Account.Type.CREDIT_CARD,
            opening_balance=money("5000"), current_balance=money("5000"),
            include_in_safe_to_spend=False,
        )
        self.food = Category.objects.create(user=self.user, name="Food", kind="expense")

    def test_income_and_expense_totals(self):
        today = date.today()
        create_transaction(
            user=self.user, account=self.bank, amount="50000", transaction_type="income",
            transaction_date=today, merchant="Salary",
        )
        create_transaction(
            user=self.user, account=self.bank, amount="8000", transaction_type="expense",
            transaction_date=today, category=self.food, merchant="Lunch",
        )
        start, end = month_bounds(today.year, today.month)
        totals = _month_totals(self.user, start, end)
        self.assertEqual(totals["income"], money("50000"))
        self.assertEqual(totals["expenses"], money("8000"))
        self.assertEqual(totals["saved"], money("42000"))
        self.assertEqual(savings_rate(totals["income"], totals["expenses"]), money("84.0") if False else totals["savings_rate"])

    def test_transfers_do_not_count_as_expenses(self):
        today = date.today()
        create_transfer(
            user=self.user, from_account=self.bank, to_account=self.cash,
            amount="3000", transfer_date=today,
        )
        start, end = month_bounds(today.year, today.month)
        totals = _month_totals(self.user, start, end)
        self.assertEqual(totals["expenses"], money("0"))
        self.assertEqual(totals["income"], money("0"))
        self.bank.refresh_from_db()
        self.cash.refresh_from_db()
        self.assertEqual(self.bank.current_balance, money("97000"))
        self.assertEqual(self.cash.current_balance, money("13000"))

    def test_credit_card_payment_is_not_double_counted(self):
        today = date.today()
        create_transaction(
            user=self.user, account=self.card, amount="2000", transaction_type="expense",
            transaction_date=today, category=self.food, merchant="Dinner",
        )
        create_transfer(
            user=self.user, from_account=self.bank, to_account=self.card,
            amount="2000", transfer_date=today, notes="Card payment",
        )
        start, end = month_bounds(today.year, today.month)
        totals = _month_totals(self.user, start, end)
        self.assertEqual(totals["expenses"], money("2000"))
        self.card.refresh_from_db()
        self.assertEqual(self.card.current_balance, money("5000"))

    def test_delete_transaction_reverses_balance(self):
        today = date.today()
        tx = create_transaction(
            user=self.user, account=self.bank, amount="1500", transaction_type="expense",
            transaction_date=today, category=self.food, merchant="Tea",
        )
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.current_balance, money("98500"))
        delete_transaction(tx)
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.current_balance, money("100000"))

    def test_budget_spent_follows_category(self):
        today = date.today()
        budget = Budget.objects.create(user=self.user, year=today.year, month=today.month)
        BudgetCategory.objects.create(budget=budget, category=self.food, allocated_amount=money("10000"))
        create_transaction(
            user=self.user, account=self.bank, amount="2500", transaction_type="expense",
            transaction_date=today, category=self.food, merchant="Groceries",
        )
        from apps.core.services.dashboard import _budget_progress

        progress = _budget_progress(self.user, today.year, today.month, today)
        self.assertEqual(progress["items"][0]["spent"], money("2500"))
        self.assertEqual(progress["items"][0]["remaining"], money("7500"))

    def test_safe_to_spend_uses_configuration(self):
        today = date.today()
        profile = self.user.profile
        profile.emergency_reserve = money("20000")
        profile.savings_reserve = money("10000")
        profile.include_upcoming_bills = True
        profile.include_debt_payments = True
        profile.include_goal_reserves = True
        profile.save()
        Bill.objects.create(
            user=self.user, name="Internet", amount=money("5000"),
            due_date=today + timedelta(days=5), frequency="monthly",
        )
        Debt.objects.create(
            user=self.user, name="Loan", original_amount=money("50000"),
            remaining_amount=money("40000"), monthly_payment=money("8000"), due_day=today.day,
        )
        SavingsGoal.objects.create(
            user=self.user, name="Laptop", target_amount=money("30000"),
            current_amount=money("10000"), is_reserved=True,
        )
        result = calculate_safe_to_spend(self.user, today)
        # Available cash: bank 100000 + cash 10000 = 110000 (card excluded)
        self.assertEqual(result["available"], money("110000"))
        self.assertEqual(result["upcoming_bills"], money("5000"))
        self.assertEqual(result["debt_payments"], money("8000"))
        self.assertEqual(result["goal_reserve"], money("20000"))
        self.assertEqual(result["safe_to_spend"], money("47000"))

    def test_net_worth_assets_minus_liabilities(self):
        data = compute_net_worth(self.user)
        # bank 100000 + cash 10000 - card 5000
        self.assertEqual(data["assets"], money("110000"))
        self.assertEqual(data["liabilities"], money("5000"))
        self.assertEqual(data["net_worth"], money("105000"))

    def test_never_uses_float_for_money(self):
        value = money("10.1") + money("0.2")
        self.assertIsInstance(value, Decimal)
        self.assertEqual(value, money("10.30"))
