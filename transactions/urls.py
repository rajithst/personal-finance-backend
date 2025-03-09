from django.urls import path
from django.urls import re_path

from transactions.apis.analytics_api import AnalyticsView
from transactions.apis.category_api import CategorySettingsView
from transactions.apis.payee_api import PayeeView, PayeeDetailView
from transactions.apis.transaction_import_api import TransactionImportView
from transactions.apis.transactions_api import TransactionView, TransactionBulkView
from transactions.apis.views import ClientSettingsView, CreditAccountView, DashboardView

urlpatterns = [
    path('dashboard/', DashboardView.as_view()),
    re_path(r'^transaction(?:/(?P<id>\d+))?/$', TransactionView.as_view()),
    re_path(r'^payee(?:/(?P<id>\d+))?/$', PayeeView.as_view()),
    path('payee-detail/<int:id>/', PayeeDetailView.as_view()),
    path('analytics/', AnalyticsView.as_view()),
    path('payee-detail/<str:name>/', PayeeDetailView.as_view()),
    path('category-settings/', CategorySettingsView.as_view()),
    path('category-settings/<int:pk>/', CategorySettingsView.as_view()),
    path('credit-account/', CreditAccountView.as_view()),
    path('bulk/transaction/', TransactionBulkView.as_view()),
    path('import/transactions/', TransactionImportView.as_view()),
    path('settings/', ClientSettingsView.as_view())
]
