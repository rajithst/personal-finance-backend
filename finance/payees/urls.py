from django.urls import path
from django.urls import re_path

from finance.payees.views import PayeeView

urlpatterns = [
    path('list/', PayeeView.as_view()),
    path('item/<int:id>/', PayeeView.as_view()),
    path('item/<str:name>/', PayeeView.as_view()),


]
