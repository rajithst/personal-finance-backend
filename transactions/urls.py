
from django.urls import path
from rest_framework.routers import SimpleRouter

from transactions.apis import views
from transactions.apis.importers import TransactionImportView

router = SimpleRouter()
router.register('income', views.IncomeViewSet)
router.register('transaction', views.TransactionViewSet, basename='transaction')
router.register('payee', views.PayeeViewSet)

urlpatterns = [
    path('dashboard', views.DashboardView.as_view()),
    path('bulk/transaction', views.TransactionBulkView.as_view()),
    path('import/transactions', TransactionImportView.as_view())
]
urlpatterns += router.urls
