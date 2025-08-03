from django.conf import settings
from django.db import models

from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    account_type = models.CharField(max_length=255, blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    provider = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    last_import_date = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'accounts_account'

    objects = RequestManager()

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)
