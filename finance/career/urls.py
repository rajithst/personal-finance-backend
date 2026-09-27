from django.urls import path
from finance.career.views import PayslipExtractView

urlpatterns = [
    path('payslips/extract/', PayslipExtractView.as_view(), name='payslip_extract'),
]
