from django.urls import path

from investments.dashboard.views import InvestmentDashboardView

urlpatterns = [
    path('', InvestmentDashboardView.as_view()),
]
