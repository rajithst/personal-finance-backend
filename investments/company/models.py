from django.db import models

from oauth.util.request_manager import CronManager


class CompanyIndustry(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_company_industry'


class CompanySector(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments_company_sector'


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

    objects = CronManager()

    cron_objects = CronManager()

    class Meta:
        db_table = 'investments_company'

    def __str__(self):
        return self.symbol
