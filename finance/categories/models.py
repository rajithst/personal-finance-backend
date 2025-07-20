from django.conf import settings
from django.db import models
from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager


class TransactionCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    category_type = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    can_rename = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'categories_transaction_category'

    objects = RequestManager()

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class TransactionSubCategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    can_rename = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'categories_transaction_subcategory'

    objects = RequestManager()

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)
