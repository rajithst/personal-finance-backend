from django.conf import settings
from django.db import models

from finance.categories.models import TransactionCategory, TransactionSubCategory
from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager


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

    objects = RequestManager()

    class Meta:
        db_table = 'payees_destination_map'

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)
