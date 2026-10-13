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
    counterparty_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='counterparty_transactions',
        help_text="Counterparty account for internal transfers or settlements (e.g. Rakuten Securities, JP Post, Wise, Credit Cards)"
    )
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
    is_third_party = models.BooleanField(default=False, db_index=True, help_text="True if transaction was performed on behalf of someone else (pass-through / proxy).")
    on_behalf_of = models.CharField(max_length=100, blank=True, null=True, help_text="Entity or person on whose behalf the transaction was performed (e.g. Wife, Family, Work).")
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
        if self.is_third_party:
            self.is_expense = False
            self.is_income = False
            self.is_saving = False
        super().save(*args, **kwargs)
