from django.contrib import admin

from apps.goals.models import GoalContribution, SavingsGoal

admin.site.register(SavingsGoal)
admin.site.register(GoalContribution)
