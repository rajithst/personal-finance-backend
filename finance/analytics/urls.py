from django.urls import path
from finance.analytics.views import AnalyticsView, AuditReportsView, SubscriptionRadarView

urlpatterns = [
    path('', AnalyticsView.as_view(), name='analytics-root'),
    path('audit-reports/', AuditReportsView.as_view(), name='analytics-audit-reports'),
    path('subscriptions/', SubscriptionRadarView.as_view(), name='analytics-subscriptions'),
]


