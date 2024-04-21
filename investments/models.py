from django.db import models

from django.db import models


class IndexFund(models.Model):
    fund_code = models.IntegerField(primary_key=True)
    fund_name = models.CharField(max_length=255)
    fund_link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Company(models.Model):
    symbol = models.CharField(max_length=10, unique=True, primary_key=True)
    company_name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    exchange = models.CharField(max_length=50)
    currency = models.CharField(max_length=5)
    country = models.CharField(max_length=100)
    website = models.URLField(max_length=255, null=True, blank=True)
    image = models.URLField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def get_market_api_fields():
        return [
            'symbol', 'companyName', 'sector', 'industry',
            'exchangeShortName', 'currency', 'country',
            'website', 'image', 'description'
        ]

    @staticmethod
    def get_field_remap():
        return {
            'exchangeShortName': 'exchange',
            'companyName': 'company_name'
        }

    def __str__(self):
        return self.symbol


class Portfolio(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    average_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class StockDailyPrice(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    change_percentage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    day_high_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    day_low_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    year_low_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    year_high_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.symbol} - {self.date}"


class IndexFundDailyPrice(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    fund_code = models.ForeignKey(IndexFund, on_delete=models.SET_NULL, null=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change_percentage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StockPurchaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class IndexFundPurchaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    fund_code = models.ForeignKey(IndexFund, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Dividend(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ex_dividend_date = models.DateField()
    payment_date = models.DateField()
    payment_received = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.company.symbol} - {self.payment_date} - ${self.amount}'

    class Meta:
        ordering = ['-payment_date']
