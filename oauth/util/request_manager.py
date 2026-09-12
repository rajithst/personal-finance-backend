from django.db import models

from oauth.middleware import get_current_user


class RequestManager(models.Manager):
    def get_queryset(self):
        current_user = get_current_user()
        if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            return super().get_queryset().filter(user_id=current_user.id)
        return super().get_queryset()


class CronManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
