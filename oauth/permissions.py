from django.conf import settings
from rest_framework import permissions


class AppEngineCronPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        is_dev_env = settings.ENV == 'dev'
        return True if is_dev_env else request.headers.get("X-Appengine-Cron") == "true"


class AppEngineTaskPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        is_dev_env = settings.ENV == 'dev'
        return True if is_dev_env else request.headers.get("Secret") == settings.SECRET_KEY
