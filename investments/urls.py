from django.urls import path

from investments.apis.company_api import CompanyValueUpdaterView
from investments.apis.dividend_api import DividendPaymentView, DividendImporterView, DividendIncomeView
from investments.apis.forex_api import DailyForexValueUpdateView
from investments.apis.stock_api import StockPurchaseHistoryView, StockDetailView, DailyStockValueUpdateView, \
    StockPurchaseImportView, BulkStockValueUpdaterView
from investments.apis.views import DashboardView

urlpatterns = [
    path('dashboard/', DashboardView.as_view()),
    path('dividends/income/', DividendIncomeView.as_view()),
    path('dividends/sync/', DividendImporterView.as_view()),
    path('dividends/payment/', DividendPaymentView.as_view()),
    path('stocks/detail/', StockDetailView.as_view()),
    path('stocks/sync/daily', DailyStockValueUpdateView.as_view()),
    path('forex/sync/daily/', DailyForexValueUpdateView.as_view()),
    path('stocks/sync/bulk/', BulkStockValueUpdaterView.as_view()),
    path('stocks/purchases/history/', StockPurchaseHistoryView.as_view()),
    path('stocks/purchases/upload/', StockPurchaseImportView.as_view()),
    path('company/sync/', CompanyValueUpdaterView.as_view()),
]

