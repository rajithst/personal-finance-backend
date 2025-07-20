from django.urls import path

from finance.reporting.views import AnalyticsView, AnalyticsPromptView

urlpatterns = [
    path('report/', AnalyticsView.as_view()),
    path('prompt/', AnalyticsPromptView.as_view()),

]
