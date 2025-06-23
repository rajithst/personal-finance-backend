from django.urls import path

from investments.apis.company_api import CompanyValueUpdaterView, CompanyListView
from investments.apis.dividend_api import DividendIncomeView, DividendCronDaemonView, DividendIncomeRefreshView, \
    DividendPaymentRefreshView
from investments.apis.forex_api import DailyForexValueDaemonView
from investments.apis.holding_api import HoldingView, HoldingValueRefreshView, HoldingDaemonView
from investments.apis.portfolio_api import PortfolioGrowthDaemonView, PortfolioSettingsView, PortfolioGrowthRefreshView
from investments.apis.stock_api import StockPriceHistoryView, DailyStockValueDaemonView, BulkStockValueUpdaterView, \
    DailyStockSplitDaemonView, StocksValueRefreshView, StocksSplitRefreshView
from investments.apis.stock_purchase_api import StockPurchaseHistoryView, StockPurchaseImportView
from investments.apis.views import InvestmentPerformanceView, ClientSettingsView

cron_endpoints = [
    path('cron/dividends/payments/', DividendCronDaemonView.as_view()),
    path('cron/stocks/market-value/', DailyStockValueDaemonView.as_view()),
    path('cron/portfolio/growth/', PortfolioGrowthDaemonView.as_view()),
    path('cron/holding/value/', HoldingDaemonView.as_view()),
    path('cron/stocks/splits/', DailyStockSplitDaemonView.as_view()),
    path('cron/forex/value/', DailyForexValueDaemonView.as_view()),
]

refresh_endpoints = [
    path('dividends/payments/refresh/', DividendPaymentRefreshView.as_view()),
    path('portfolio/growth/refresh/', PortfolioGrowthRefreshView.as_view()),
    path('portfolio/holdings/refresh/', HoldingValueRefreshView.as_view()),
    path('stocks/value/refresh/', StocksValueRefreshView.as_view()),
    path('splits/value/refresh/', StocksSplitRefreshView.as_view()),
    path('dividends/income/refresh/', DividendIncomeRefreshView.as_view()),
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
                  path('portfolio/', PortfolioSettingsView.as_view()),
                  path('settings/', ClientSettingsView.as_view())

              ] + cron_endpoints + upload_endpoints + data_fill_endpoints + refresh_endpoints
