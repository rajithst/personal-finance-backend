from django.urls import path

from finance.reporting.views import AnalyticsView

urlpatterns = [
    path('report/', AnalyticsView.as_view()),
]
