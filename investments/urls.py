
from rest_framework.routers import SimpleRouter

from investments import views

router = SimpleRouter()
router.register('stock/purchase-history', views.StockPurchaseHistoryViewSet)
router.register('company', views.CompanyViewSet)

urlpatterns = [
]
urlpatterns += router.urls
