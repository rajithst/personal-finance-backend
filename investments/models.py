from django.conf import settings
from django.db import models

from oauth.middleware import get_current_user
from transactions.models import Account


class RequestManager(models.Manager):
    def get_queryset(self):
        current_user = get_current_user()
        if current_user:
            return super().get_queryset().filter(user_id=current_user.id)


class CronManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class CompanyIndustry(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class CompanySector(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Portfolio(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    currency = models.CharField(max_length=50, null=True, blank=True)
    goal = models.CharField(max_length=50, null=True, blank=True)
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    cron_objects = CronManager()

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class Company(models.Model):
    symbol = models.CharField(max_length=10, unique=True, primary_key=True)
    company_name = models.CharField(max_length=255)
    sector = models.ForeignKey(CompanySector, on_delete=models.CASCADE)
    industry = models.ForeignKey(CompanyIndustry, on_delete=models.CASCADE)
    exchange = models.CharField(max_length=50)
    currency = models.CharField(max_length=5)
    country = models.CharField(max_length=100)
    website = models.URLField(max_length=255, null=True, blank=True)
    image = models.URLField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    cron_objects = CronManager()

    def __str__(self):
        return self.symbol


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
        ordering = ['-purchase_date']

    objects = RequestManager()

    cron_objects = CronManager()

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class IndexFund(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255, null=True, blank=True)
    english_name = models.CharField(max_length=255, null=True, blank=True)
    link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


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

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class IndexFundHolding(models.Model):
    id = models.AutoField(primary_key=True)
    fund = models.ForeignKey(IndexFund, on_delete=models.CASCADE, null=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class DividendHistory(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ex_dividend_date = models.DateField(blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class DividendPayment(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    payment_date = models.DateField(blank=True, null=True)
    ex_dividend_date = models.DateField(blank=True, null=True)
    payment_received = models.BooleanField(default=False)
    pre_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

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
    def __str__(self):
        return f"{self.company.symbol} - {self.split_date}"


class IndexFundDailyPrice(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    index_fund = models.ForeignKey(IndexFund, on_delete=models.SET_NULL, null=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change_percentage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class IndexFundPurchaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_date = models.DateField(null=True, blank=True)
    fund = models.ForeignKey(IndexFund, on_delete=models.SET_NULL, null=True, blank=True)
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

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class PortfolioDailyGrowth(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    total_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    portfolio_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    daily_return = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    cron_objects = CronManager()


class Forex(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=10, unique=True, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
