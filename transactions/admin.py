from django.contrib import admin
from . import models


@admin.register(models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['category', 'account', 'amount', 'date', 'notes', ]
    search_fields = ['category__startswith', 'amount__startswith', 'date__startswith']

@admin.register(models.TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['category']


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['account_name', 'description']
