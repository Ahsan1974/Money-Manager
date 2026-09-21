import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.accounts.models import Account, Investment, Transfer
from apps.ai.models import AIConversation
from apps.analytics.models import NetWorthSnapshot
from apps.bills.models import Bill, Subscription
from apps.core.models import Notification, Person
from apps.core.services.defaults import ensure_user_defaults
from apps.debts.models import Debt, LendingRecord
from apps.goals.models import SavingsGoal
from apps.transactions.models import Transaction


class Command(BaseCommand):
    help = "Create or reset the personal workspace with no sample transactions."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.getenv("OWNER_USERNAME", "ahsan"))
        parser.add_argument("--password", default=os.getenv("OWNER_PASSWORD", ""))
        parser.add_argument("--name", default=os.getenv("OWNER_DISPLAY_NAME", "Ahsan Nadeem"))
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        username = options["username"]
        display_name = options["name"]
        password = options["password"]
        parts = display_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        user = User.objects.filter(username__in=[username, "demo", "ali"]).first()
        created = False
        if user is None:
            if not password:
                raise SystemExit("Set OWNER_PASSWORD in .env (or pass --password) to create the owner account.")
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email="ahsan@localhost",
            )
            created = True
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            if password:
                user.set_password(password)
            user.save()

        profile = user.profile
        profile.display_name = display_name
        profile.emergency_reserve = 0
        profile.savings_reserve = 0
        profile.save()
        ensure_user_defaults(user)

        if options["reset"] or not created:
            Transaction.objects.filter(user=user).delete()
            Transfer.objects.filter(user=user).delete()
            Account.objects.filter(user=user).delete()
            user.budgets.all().delete()
            SavingsGoal.objects.filter(user=user).delete()
            Bill.objects.filter(user=user).delete()
            Subscription.objects.filter(user=user).delete()
            Debt.objects.filter(user=user).delete()
            LendingRecord.objects.filter(user=user).delete()
            Investment.objects.filter(user=user).delete()
            Person.objects.filter(user=user).delete()
            Notification.objects.filter(user=user).delete()
            NetWorthSnapshot.objects.filter(user=user).delete()
            AIConversation.objects.filter(user=user).delete()

        self.stdout.write(self.style.SUCCESS(f"Workspace ready for {display_name} ({username}). No sample money data."))
