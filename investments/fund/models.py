from django.conf import settings
from django.db import models

from accounts.models import Account
from investments.portfolio.models import Portfolio
from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager


class Fund(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255, null=True, blank=True)
    english_name = models.CharField(max_length=255, null=True, blank=True)
    link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_fund'


class FundHolding(models.Model):
    id = models.AutoField(primary_key=True)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    average_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fund_currency = models.CharField(max_length=12, null=True, blank=True)
    price_updated_at = models.DateField(null=True, blank=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'investments_fund_holding'

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class FundDailyPrice(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    index_fund = models.ForeignKey(Fund, on_delete=models.SET_NULL, null=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change_percentage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_fund_daily_price'


class FundPurchaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_date = models.DateField(null=True, blank=True)
    fund = models.ForeignKey(Fund, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    settlement_currency = models.CharField(max_length=12, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'investments_fund_purchase_history'

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)
