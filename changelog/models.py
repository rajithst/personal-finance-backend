from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ActionEnum(models.TextChoices):
    CREATE = 'create', 'Created'
    UPDATE = 'update', 'Updated'
    DELETE = 'delete', 'Deleted'
    MERGE = 'merge', 'Merged'
    SPLIT = 'split', 'Split'
    BULK_DELETE = 'bulk delete', 'Bulk Deleted'


class SectionEnum(models.TextChoices):
    TRANSACTION = 'transaction', 'Transaction'
    CATEGORY = 'category', 'Category'
    SUBCATEGORY = 'subcategory', 'Subcategory'
    PAYEE = 'payee', 'Payee'
    ACCOUNT = 'account', 'Account'
    STOCK = 'stock', 'Stock'
    DIVIDEND = 'dividend', 'Dividend'


class ChangeLog(models.Model):
    id = models.AutoField(primary_key=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    section = models.CharField(choices=SectionEnum, max_length=50)
    action = models.CharField(choices=ActionEnum, max_length=50)
    changelog = models.JSONField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
