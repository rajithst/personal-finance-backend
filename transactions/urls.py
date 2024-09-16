from django.urls import path
from django.urls import re_path
from transactions.apis import views
from transactions.apis.importers import TransactionImportView
from transactions.apis.views import ClientSettingsView

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view()),
    re_path(r'^transaction(?:/(?P<id>\d+))?/$', views.TransactionView.as_view()),
    re_path(r'^payee(?:/(?P<id>\d+))?/$', views.PayeeView.as_view()),
    path('payee-detail/<int:id>/', views.PayeeDetailView.as_view()),
    path('payee-detail/<str:name>/', views.PayeeDetailView.as_view()),
    path('category-settings/', views.CategorySettingsView.as_view()),
    path('bulk/transaction/', views.TransactionBulkView.as_view()),
    path('import/transactions/', TransactionImportView.as_view()),
    path('settings/', ClientSettingsView.as_view())
]
