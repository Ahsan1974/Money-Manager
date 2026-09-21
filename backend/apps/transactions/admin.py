from django.contrib import admin

from apps.transactions.models import Category, Receipt, Transaction

admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Receipt)
