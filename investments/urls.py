from django.urls import path
from rest_framework.routers import SimpleRouter

from investments.apis.updaters import StockDailyUpdaterView, ForexDailyUpdaterView, CompanyDataUpdaterView, \
    DividendDailyUpdaterView, HistoricalStockDataUpdaterView
from investments.apis.importers import TradeImportView
from investments.apis.views import StockPurchaseHistoryViewSet, DividendViewSet, CompanyViewSet, \
    InvestmentsView, StockDetailView

router = SimpleRouter()
router.register(r'stock-purchase-history', StockPurchaseHistoryViewSet)
router.register(r'dividend', DividendViewSet)
router.register(r'company', CompanyViewSet)
urlpatterns = [
    path('list', InvestmentsView.as_view()),
    path('refresh/stock-data', StockDailyUpdaterView.as_view()),
    path('stock-summary/<str:symbol>/', StockDetailView.as_view()),
    path('refresh/histoical-stock-data', HistoricalStockDataUpdaterView.as_view()),
    path('refresh/forex-data', ForexDailyUpdaterView.as_view()),
    path('refresh/company-data', CompanyDataUpdaterView.as_view()),
    path('refresh/dividend-data', DividendDailyUpdaterView.as_view()),
    path('prepare/dividend-payment', DividendDailyUpdaterView.as_view()),
    path('import/trade/', TradeImportView.as_view()),
] + router.urls
