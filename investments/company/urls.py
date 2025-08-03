from django.urls import path

from investments.company.views import CompanyListView, CompanyValueUpdaterView

urlpatterns = [
    path('list/', CompanyListView.as_view()),
    path('detail/fetch/', CompanyValueUpdaterView.as_view()),

]
