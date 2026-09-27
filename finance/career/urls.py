from django.urls import path
from finance.career.views import PayslipExtractView, PayslipSaveView

urlpatterns = [
    path('payslips/extract/', PayslipExtractView.as_view(), name='payslip_extract'),
    path('payslips/save/', PayslipSaveView.as_view(), name='payslip_save'),
]
