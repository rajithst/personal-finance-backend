from django.urls import path

from finance.dashboard.views import DashboardView

urlpatterns = [
    path('', DashboardView.as_view()),
]
