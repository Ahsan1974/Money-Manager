from django.contrib import admin

from apps.accounts.models import Account, Investment, Transfer

admin.site.register(Account)
admin.site.register(Transfer)
admin.site.register(Investment)
