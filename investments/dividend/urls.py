from django.urls import path

from investments.dividend.views import DividendPaymentRefreshView, DividendCronDaemonView, DividendIncomeRefreshView, \
    DividendIncomeView

urlpatterns = [
    path('payments/refresh/', DividendPaymentRefreshView.as_view()),
    path('cron/payments/', DividendCronDaemonView.as_view()),
    path('income/refresh/', DividendIncomeRefreshView.as_view()),
    path('income/', DividendIncomeView.as_view()),
]
