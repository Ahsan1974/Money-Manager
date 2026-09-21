from django.contrib import admin

from apps.debts.models import Debt, LendingRecord

admin.site.register(Debt)
admin.site.register(LendingRecord)
