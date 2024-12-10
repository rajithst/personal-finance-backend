from django.urls import path

from investments.apis.company_api import CompanyValueUpdaterView
from investments.apis.dividend_api import DividendIncomeView, DividendPaymentUpdaterView, DividendImporterView
from investments.apis.forex_api import DailyForexValueUpdateView
from investments.apis.holding_api import HoldingView
from investments.apis.stock_api import StockPurchaseHistoryView, StockDetailView, DailyStockValueUpdateView, \
    StockPurchaseImportView, BulkStockValueUpdaterView
from investments.apis.views import PortfolioView, InvestmentPerformanceView

urlpatterns = [
    path('dashboard/', InvestmentPerformanceView.as_view()),
    path('portfolio/', PortfolioView.as_view()),
    path('holdings/', HoldingView.as_view()),
    path('dividends/income/', DividendIncomeView.as_view()),
    path('stocks/detail/', StockDetailView.as_view()),
    path('dividends/sync/daily/', DividendPaymentUpdaterView.as_view()),
    path('stocks/sync/daily', DailyStockValueUpdateView.as_view()),
    path('forex/sync/daily/', DailyForexValueUpdateView.as_view()),
    path('stocks/sync/bulk/', BulkStockValueUpdaterView.as_view()),
    path('dividend/payment/import', DividendImporterView),
    path('stocks/purchases/history/', StockPurchaseHistoryView.as_view()),
    path('stocks/purchases/upload/', StockPurchaseImportView.as_view()),
    path('company/sync/', CompanyValueUpdaterView.as_view()),
]
