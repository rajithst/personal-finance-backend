from django.urls import path
from rest_framework.routers import SimpleRouter

from investments import views

router = SimpleRouter()
router.register('stock-purchase-history', views.StockPurchaseHistoryViewSet)
router.register('company', views.CompanyViewSet)

urlpatterns = [
    path('list', views.InvestmentsView.as_view())
]
urlpatterns += router.urls
