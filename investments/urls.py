from django.urls import path

from investments.apis.company_api import CompanyValueUpdaterView, CompanyListView
from investments.apis.dividend_api import DividendIncomeView, \
    DividendPaymentDaemonView, DividendIncomeDaemonView
from investments.apis.forex_api import DailyForexValueDaemonView
from investments.apis.holding_api import HoldingView
from investments.apis.stock_api import StockPriceHistoryView, DailyStockValueDaemonView, BulkStockValueUpdaterView
from investments.apis.stock_purchase_api import StockPurchaseHistoryView, StockPurchaseImportView
from investments.apis.views import InvestmentPerformanceView, ClientSettingsView

cron_endpoints = [
    path('dividend/cron/payments/daily/', DividendPaymentDaemonView.as_view()),
    path('dividends/cron/income/daily/', DividendIncomeDaemonView.as_view()),
    path('stocks/cron/value/daily', DailyStockValueDaemonView.as_view()),
    path('forex/cron/value/daily/', DailyForexValueDaemonView.as_view()),
]

upload_endpoints = [
    path('stocks/purchases/upload/', StockPurchaseImportView.as_view()),
]

data_fill_endpoints = [
    path('company/detail/fetch/', CompanyValueUpdaterView.as_view()),
    path('stocks/historical-data/fetch/', BulkStockValueUpdaterView.as_view()),
]

urlpatterns = [
    path('dashboard/', InvestmentPerformanceView.as_view()),
    path('holdings/', HoldingView.as_view()),
    path('dividends/income/', DividendIncomeView.as_view()),
    path('stocks/price/history/', StockPriceHistoryView.as_view()),
    path('company/list/', CompanyListView.as_view()),
    path('stocks/purchase/history/', StockPurchaseHistoryView.as_view()),
    path('settings/', ClientSettingsView.as_view())


] + cron_endpoints + upload_endpoints + data_fill_endpoints
