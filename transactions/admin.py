from django.contrib import admin
from . import models


@admin.register(models.Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount', 'date', 'notes']
    search_fields = ['category__startswith', 'amount__startswith', 'date__startswith']
    list_filter = ['category']

    def target_month_text(self, obj):
        month_map = {
            1: 'January',
            2: 'February',
            3: 'March',
            4: 'April',
            5: 'May',
            6: 'June',
            7: 'July',
            8: 'August',
            9: 'September',
            10: 'October',
            11: 'November',
            12: 'December'
        }

        if obj.target_month:
            return month_map[obj.target_month]
        else:
            return ''


@admin.register(models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['category', 'payment_method', 'amount', 'date', 'notes', ]
    search_fields = ['category__startswith', 'amount__startswith', 'date__startswith']


@admin.register(models.IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ['category']


@admin.register(models.TransactionCategory)
class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['category']


@admin.register(models.PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
