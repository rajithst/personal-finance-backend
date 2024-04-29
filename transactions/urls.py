
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from transactions import views

router = SimpleRouter()
router.register('income', views.IncomeViewSet)

urlpatterns = [
    path('transactions/', views.TransactionsView.as_view()),
    path('transactions/import/', views.TransactionImportView.as_view())
]
urlpatterns += router.urls
