from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from oauth.models import User


# Register your models here.

@admin.register(User)
class UserAdmin(UserAdmin):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "email", "first_name", "last_name"),
            },
        ),
    )