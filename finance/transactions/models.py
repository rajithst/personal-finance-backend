from django.conf import settings
from django.db import models

from accounts.models import Account
from finance.categories.models import TransactionCategory, TransactionSubCategory
from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager


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

    objects = RequestManager()

    class Meta:
        db_table = 'transactions_transaction'

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)
