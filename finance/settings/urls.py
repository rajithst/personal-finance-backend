from django.urls import path

from finance.settings.views import ClientSettings

urlpatterns = [
    path('', ClientSettings.as_view())
]
