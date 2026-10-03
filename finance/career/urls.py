from django.urls import path
from finance.career.views import (
    CompanyProfileView,
    EmploymentView,
    DispatchAssignmentView,
    CompensationHistoryView,
    CareerDocumentView,
    CareerDocumentDownloadView,
    MonthlyPayslipView,
    TaxWithholdingSlipView,
    CareerOverviewView,
    PayslipExtractView,
    PayslipSaveView,
    PayslipAnalyticsView
)

urlpatterns = [
    # Career Overview & Analytics
    path('overview/', CareerOverviewView.as_view(), name='career-overview'),

    # Company Profiles
    path('companies/', CompanyProfileView.as_view(), name='career-companies-list'),
    path('companies/<int:pk>/', CompanyProfileView.as_view(), name='career-company-detail'),

    # Employment Tenures
    path('employments/', EmploymentView.as_view(), name='career-employments-list'),
    path('employments/<int:pk>/', EmploymentView.as_view(), name='career-employment-detail'),

    # Dispatch / Client Assignments
    path('dispatches/', DispatchAssignmentView.as_view(), name='career-dispatches-list'),
    path('dispatches/<int:pk>/', DispatchAssignmentView.as_view(), name='career-dispatch-detail'),

    # Compensation History
    path('compensations/', CompensationHistoryView.as_view(), name='career-compensations-list'),
    path('compensations/<int:pk>/', CompensationHistoryView.as_view(), name='career-compensation-detail'),

    # Monthly Payslips (給与明細)
    path('payslips/analytics/', PayslipAnalyticsView.as_view(), name='career-payslips-analytics'),
    path('payslips/', MonthlyPayslipView.as_view(), name='career-payslips-list'),
    path('payslips/<int:pk>/', MonthlyPayslipView.as_view(), name='career-payslip-detail'),

    # Withholding Tax Slips (源泉徴収票)
    path('tax-slips/', TaxWithholdingSlipView.as_view(), name='career-tax-slips-list'),
    path('tax-slips/<int:pk>/', TaxWithholdingSlipView.as_view(), name='career-tax-slip-detail'),

    # Document Vault
    path('documents/', CareerDocumentView.as_view(), name='career-documents-list'),
    path('documents/<int:pk>/', CareerDocumentView.as_view(), name='career-document-detail'),
    path('documents/<int:pk>/download/', CareerDocumentDownloadView.as_view(), name='career-document-download'),
    
    path('payslips/extract/', PayslipExtractView.as_view(), name='career-payslip-extract'),
    path('payslips/save/', PayslipSaveView.as_view(), name='career-payslip-save'),
]
