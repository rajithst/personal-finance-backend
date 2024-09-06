
from django.urls import path
from rest_framework.routers import SimpleRouter

from transactions.apis import views
from transactions.apis.importers import TransactionImportView
from transactions.apis.views import ClientSettingsView

router = SimpleRouter()
router.register('transaction', views.TransactionViewSet, basename='transaction')
router.register('payee', views.PayeeViewSet)

urlpatterns = [
    path('dashboard', views.DashboardView.as_view()),
    path('payee/id/<int:id>', views.PayeeViewSet.as_view({'get': 'retrieve'})),
    path('payee/name/<str:name>', views.PayeeViewSet.as_view({'get': 'retrieve'})),
    path('bulk/transaction', views.TransactionBulkView.as_view()),
    path('import/transactions', TransactionImportView.as_view()),
    path('settings', ClientSettingsView.as_view())
]
urlpatterns += router.urls
