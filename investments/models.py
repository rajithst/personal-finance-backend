from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date']


class Holding(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    average_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_investment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_currency = models.CharField(max_length=12, null=True, blank=True)
    price_updated_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Dividend(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ex_dividend_date = models.DateField(blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    payment_received = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.company.symbol} - {self.payment_date} - ${self.amount}'

    class Meta:
        ordering = ['-payment_date']


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


class IndexFund(models.Model):
    fund_code = models.IntegerField(primary_key=True)
    fund_name = models.CharField(max_length=255)
    fund_link = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class IndexFundDailyPrice(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    fund_code = models.ForeignKey(IndexFund, on_delete=models.SET_NULL, null=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    change_percentage = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class IndexFundPurchaseHistory(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_date = models.DateField(null=True, blank=True)
    fund_code = models.ForeignKey(IndexFund, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    settlement_currency = models.CharField(max_length=12, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class Forex(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=10, unique=True, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
