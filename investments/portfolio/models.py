from django.conf import settings
from django.db import models

from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager, CronManager


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

    class Meta:
        db_table = 'investments_portfolio'

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

    class Meta:
        db_table = 'investments_portfolio_daily_growth'
