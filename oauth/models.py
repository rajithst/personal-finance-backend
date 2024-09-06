import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    is_premium = models.BooleanField(default=False)
    premium_plan = models.CharField(max_length=255, blank=True, null=True)
    onboarding = models.BooleanField(default=False)
    profile_picture = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(blank=True, null=True)
    two_factor_enabled = models.BooleanField(default=False)
    theme = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
