from django.urls import path

from accounts.views import CreditAccountView

urlpatterns = [
    path('credit/', CreditAccountView.as_view()),
]
