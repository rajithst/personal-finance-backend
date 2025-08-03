from django.urls import path

from investments.portfolio.views import PortfolioGrowthDaemonView, PortfolioGrowthRefreshView, PortfolioSettingsView

urlpatterns = [
    path('', PortfolioSettingsView.as_view()),
    path('cron/growth/', PortfolioGrowthDaemonView.as_view()),
    path('growth/refresh/', PortfolioGrowthRefreshView.as_view()),
]
