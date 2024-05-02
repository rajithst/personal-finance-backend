from django.urls import path
from rest_framework.routers import SimpleRouter

from investments import views

urlpatterns = [
    path('list', views.InvestmentsView.as_view()),
    path('stock-purchase/', views.StockPurchaseHistoryView.as_view()),
    path('stock-data-update/', views.StockDailyUpdaterView.as_view()),
    path('forex-data-update/', views.ForexDailyUpdaterView.as_view()),
    path('company-data-update/', views.CompanyDataUpdaterView.as_view()),
    path('dividend-data-update/', views.DividendDailyUpdaterView.as_view()),
    path('import-broker-data/', views.TradeImportView.as_view()),
]
