from django.conf import settings
from django.db import models

from accounts.models import Account
from investments.company.models import Company
from investments.portfolio.models import Portfolio
from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager, CronManager


class Holding(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    average_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_currency = models.CharField(max_length=12, null=True, blank=True)
    price_updated_at = models.DateField(null=True, blank=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    cron_objects = CronManager()

    class Meta:
        db_table = 'investments_holding'

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class StockPurchaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_date = models.DateField(null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    settlement_currency = models.CharField(max_length=12, null=True, blank=True)
    stock_currency = models.CharField(max_length=12, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_stock_purchase_history'
        ordering = ['-purchase_date']

    objects = RequestManager()

    cron_objects = CronManager()

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class StockDailyPrice(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    change_percentage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    day_high_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    day_low_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    cron_objects = CronManager()

    class Meta:
        db_table = 'investments_stock_daily_price'

    def __str__(self):
        return f"{self.company.symbol} - {self.date}"


class StockSplit(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    split_date = models.DateField()
    split_ratio = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    cron_objects = CronManager()

    class Meta:
        db_table = 'investments_stock_split'
        ordering = ['-split_date']

    def __str__(self):
        return f"{self.company.symbol} - {self.split_date}"
