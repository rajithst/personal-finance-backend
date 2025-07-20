from django.urls import path
from django.urls import re_path

from finance.transactions.views import TransactionView, TransactionBulkView, TransactionImportView

urlpatterns = [
    path('item/', TransactionView.as_view()),
    path('item/<int:id>/', TransactionView.as_view()),
    path('list/', TransactionView.as_view()),
    path('bulk/transaction/', TransactionBulkView.as_view()),
    path('import/transactions/', TransactionImportView.as_view()),

]
