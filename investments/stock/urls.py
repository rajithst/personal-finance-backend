from django.urls import path

from investments.stock.api.holding_api import HoldingValueRefreshView, HoldingDaemonView, HoldingView
from investments.stock.api.stock_api import DailyStockValueDaemonView, DailyStockSplitDaemonView, \
    StocksValueRefreshView, StocksSplitRefreshView, BulkStockValueUpdaterView, StockPriceHistoryView
from investments.stock.api.stock_purchase_api import StockPurchaseImportView, StockPurchaseHistoryView

urlpatterns = [
    path('holdings/refresh/', HoldingValueRefreshView.as_view()),
    path('cron/market-value/', DailyStockValueDaemonView.as_view()),
    path('cron/holding/value/', HoldingDaemonView.as_view()),
    path('cron/splits/', DailyStockSplitDaemonView.as_view()),
    path('value/refresh/', StocksValueRefreshView.as_view()),
    path('splits/refresh/', StocksSplitRefreshView.as_view()),
    path('purchases/upload/', StockPurchaseImportView.as_view()),
    path('historical-data/fetch/', BulkStockValueUpdaterView.as_view()),
    path('holdings/', HoldingView.as_view()),
    path('price/history/', StockPriceHistoryView.as_view()),
    path('purchase/history/', StockPurchaseHistoryView.as_view()),

]
