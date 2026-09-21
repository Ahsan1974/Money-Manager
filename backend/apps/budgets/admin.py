from django.contrib import admin

from apps.budgets.models import Budget, BudgetCategory

admin.site.register(Budget)
admin.site.register(BudgetCategory)
