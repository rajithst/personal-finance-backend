from django.urls import path

from investments.settings.views import ClientSettingsView

urlpatterns = [
    path('', ClientSettingsView.as_view())
]
