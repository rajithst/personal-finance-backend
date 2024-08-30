import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    is_premium = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

