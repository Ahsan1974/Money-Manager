from django.contrib import admin

from apps.bills.models import Bill, Subscription

admin.site.register(Bill)
admin.site.register(Subscription)
