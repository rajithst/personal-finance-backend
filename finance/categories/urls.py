from django.urls import path

from finance.categories.views import CategorySettingsView

urlpatterns = [
    path('settings/', CategorySettingsView.as_view()),
    path('settings/<int:pk>/', CategorySettingsView.as_view())
]
