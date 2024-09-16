from django.db import models
from django.conf import settings


class TransactionCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    category_type = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    can_rename = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)


class TransactionSubCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    can_rename = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    account_type = models.CharField(max_length=255, blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    provider = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    last_import_date = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)


class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(TransactionSubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    destination_original = models.CharField(max_length=255, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    alias = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(default=None, blank=True, null=True)
    is_saving = models.BooleanField(default=False)
    is_income = models.BooleanField(default=False)
    is_payment = models.BooleanField(default=False)
    is_expense = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_merge = models.BooleanField(default=False)
    merge_id = models.IntegerField(default=None, blank=True, null=True)
    delete_reason = models.TextField(default=None, blank=True, null=True)
    source = models.IntegerField(default=0, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.amount) + " " + str(self.date)


class DestinationMap(models.Model):
    id = models.AutoField(primary_key=True)
    destination_original = models.CharField(max_length=255, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    destination_eng = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    category_type = models.IntegerField(blank=True, null=True)
    subcategory = models.ForeignKey(TransactionSubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
