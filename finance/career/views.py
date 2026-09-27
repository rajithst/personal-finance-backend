from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from finance.career.models import (
    CompanyProfile,
    Employment,
    DispatchAssignment,
    CareerDocument,
    CompensationHistory,
    MonthlyPayslip,
    TaxWithholdingSlip,
)
from finance.career.serializers import (
    CompanyProfileSerializer,
    EmploymentSerializer,
    DispatchAssignmentSerializer,
    CareerDocumentSerializer,
    CompensationHistorySerializer,
    MonthlyPayslipSerializer,
    TaxWithholdingSlipSerializer,
)


class CompanyProfileView(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                company = CompanyProfile.objects.filter(pk=pk).first()
                if not company:
                    return Response({'data': None, 'status': False, 'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = CompanyProfileSerializer(company)
                return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

            companies = CompanyProfile.objects.all().order_by('name')
            company_type = request.query_params.get('type')
            if company_type:
                companies = companies.filter(company_type=company_type)

            serializer = CompanyProfileSerializer(companies, many=True)
            return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = CompanyProfileSerializer(data=request.data)
            if serializer.is_valid():
                company = serializer.save()
                return Response({'data': CompanyProfileSerializer(company).data, 'status': True, 'message': 'Company created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk=None):
        try:
            company = CompanyProfile.objects.filter(pk=pk).first()
            if not company:
                return Response({'data': None, 'status': False, 'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = CompanyProfileSerializer(company, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response({'data': CompanyProfileSerializer(updated).data, 'status': True, 'message': 'Company updated successfully'}, status=status.HTTP_200_OK)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            company = CompanyProfile.objects.filter(pk=pk).first()
            if not company:
                return Response({'data': None, 'status': False, 'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
            company.delete()
            return Response({'data': None, 'status': True, 'message': 'Company deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmploymentView(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                emp = (
                    Employment.objects.select_related('company')
                    .prefetch_related(
                        'dispatch_assignments__dispatched_company',
                        'compensation_history',
                        'documents',
                        'payslips',
                        'tax_slips'
                    )
                    .filter(pk=pk)
                    .first()
                )
                if not emp:
                    return Response({'data': None, 'status': False, 'message': 'Employment record not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = EmploymentSerializer(emp)
                return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

            employments = (
                Employment.objects.select_related('company')
                .prefetch_related(
                    'dispatch_assignments__dispatched_company',
                    'compensation_history',
                    'documents',
                    'payslips',
                    'tax_slips'
                )
                .all()
                .order_by('-start_date')
            )
            serializer = EmploymentSerializer(employments, many=True)
            return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = EmploymentSerializer(data=request.data)
            if serializer.is_valid():
                emp = serializer.save()
                return Response({'data': EmploymentSerializer(emp).data, 'status': True, 'message': 'Employment created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk=None):
        try:
            emp = Employment.objects.filter(pk=pk).first()
            if not emp:
                return Response({'data': None, 'status': False, 'message': 'Employment record not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = EmploymentSerializer(emp, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response({'data': EmploymentSerializer(updated).data, 'status': True, 'message': 'Employment updated successfully'}, status=status.HTTP_200_OK)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            emp = Employment.objects.filter(pk=pk).first()
            if not emp:
                return Response({'data': None, 'status': False, 'message': 'Employment record not found'}, status=status.HTTP_404_NOT_FOUND)
            emp.delete()
            return Response({'data': None, 'status': True, 'message': 'Employment deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DispatchAssignmentView(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                dispatch = DispatchAssignment.objects.select_related('dispatched_company', 'employment__company').filter(pk=pk).first()
                if not dispatch:
                    return Response({'data': None, 'status': False, 'message': 'Dispatch assignment not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = DispatchAssignmentSerializer(dispatch)
                return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

            dispatches = DispatchAssignment.objects.select_related('dispatched_company', 'employment__company').all().order_by('-start_date')
            employment_id = request.query_params.get('employment_id')
            if employment_id:
                dispatches = dispatches.filter(employment_id=employment_id)

            serializer = DispatchAssignmentSerializer(dispatches, many=True)
            return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = DispatchAssignmentSerializer(data=request.data)
            if serializer.is_valid():
                dispatch = serializer.save()
                return Response({'data': DispatchAssignmentSerializer(dispatch).data, 'status': True, 'message': 'Dispatch assignment created successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk=None):
        try:
            dispatch = DispatchAssignment.objects.filter(pk=pk).first()
            if not dispatch:
                return Response({'data': None, 'status': False, 'message': 'Dispatch assignment not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = DispatchAssignmentSerializer(dispatch, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response({'data': DispatchAssignmentSerializer(updated).data, 'status': True, 'message': 'Dispatch assignment updated successfully'}, status=status.HTTP_200_OK)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            dispatch = DispatchAssignment.objects.filter(pk=pk).first()
            if not dispatch:
                return Response({'data': None, 'status': False, 'message': 'Dispatch assignment not found'}, status=status.HTTP_404_NOT_FOUND)
            dispatch.delete()
            return Response({'data': None, 'status': True, 'message': 'Dispatch assignment deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CareerDocumentView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, pk=None):
        try:
            if pk:
                doc = CareerDocument.objects.select_related('company', 'employment').filter(pk=pk).first()
                if not doc:
                    return Response({'data': None, 'status': False, 'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = CareerDocumentSerializer(doc)
                return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

            docs = CareerDocument.objects.select_related('company', 'employment').all().order_by('-issue_date', '-created_at')
            doc_type = request.query_params.get('type')
            company_id = request.query_params.get('company_id')
            employment_id = request.query_params.get('employment_id')
            year = request.query_params.get('year')

            if doc_type:
                docs = docs.filter(document_type=doc_type)
            if company_id:
                docs = docs.filter(company_id=company_id)
            if employment_id:
                docs = docs.filter(employment_id=employment_id)
            if year:
                docs = docs.filter(issue_date__year=year)

            serializer = CareerDocumentSerializer(docs, many=True)
            return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            file_obj = request.FILES.get('file')
            data = request.data.copy()

            if file_obj:
                data['file_name_original'] = file_obj.name
                data['file_size'] = file_obj.size
                data['mime_type'] = getattr(file_obj, 'content_type', '')

            serializer = CareerDocumentSerializer(data=data)
            if serializer.is_valid():
                doc = serializer.save()
                return Response({'data': CareerDocumentSerializer(doc).data, 'status': True, 'message': 'Document uploaded successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            doc = CareerDocument.objects.filter(pk=pk).first()
            if not doc:
                return Response({'data': None, 'status': False, 'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
            if doc.file:
                doc.file.delete(save=False)
            doc.delete()
            return Response({'data': None, 'status': True, 'message': 'Document deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompensationHistoryView(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                comp = CompensationHistory.objects.select_related('employment__company').filter(pk=pk).first()
                if not comp:
                    return Response({'data': None, 'status': False, 'message': 'Compensation record not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = CompensationHistorySerializer(comp)
                return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

            compensations = CompensationHistory.objects.select_related('employment__company').all().order_by('-effective_date')
            employment_id = request.query_params.get('employment_id')
            if employment_id:
                compensations = compensations.filter(employment_id=employment_id)

            serializer = CompensationHistorySerializer(compensations, many=True)
            return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = CompensationHistorySerializer(data=request.data)
            if serializer.is_valid():
                comp = serializer.save()
                return Response({'data': CompensationHistorySerializer(comp).data, 'status': True, 'message': 'Compensation revision logged successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk=None):
        try:
            comp = CompensationHistory.objects.filter(pk=pk).first()
            if not comp:
                return Response({'data': None, 'status': False, 'message': 'Compensation record not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = CompensationHistorySerializer(comp, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response({'data': CompensationHistorySerializer(updated).data, 'status': True, 'message': 'Compensation revision updated successfully'}, status=status.HTTP_200_OK)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            comp = CompensationHistory.objects.filter(pk=pk).first()
            if not comp:
                return Response({'data': None, 'status': False, 'message': 'Compensation record not found'}, status=status.HTTP_404_NOT_FOUND)
            comp.delete()
            return Response({'data': None, 'status': True, 'message': 'Compensation revision deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MonthlyPayslipView(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                slip = MonthlyPayslip.objects.select_related('employment__company', 'document').filter(pk=pk).first()
                if not slip:
                    return Response({'data': None, 'status': False, 'message': 'Payslip not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = MonthlyPayslipSerializer(slip)
                return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

            payslips = MonthlyPayslip.objects.select_related('employment__company', 'document').all().order_by('-year', '-month')
            employment_id = request.query_params.get('employment_id')
            year = request.query_params.get('year')
            month = request.query_params.get('month')
            is_bonus = request.query_params.get('is_bonus')

            if employment_id:
                payslips = payslips.filter(employment_id=employment_id)
            if year:
                payslips = payslips.filter(year=year)
            if month:
                payslips = payslips.filter(month=month)
            if is_bonus is not None:
                payslips = payslips.filter(is_bonus=is_bonus.lower() in ['true', '1'])

            serializer = MonthlyPayslipSerializer(payslips, many=True)
            return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = MonthlyPayslipSerializer(data=request.data)
            if serializer.is_valid():
                slip = serializer.save()
                return Response({'data': MonthlyPayslipSerializer(slip).data, 'status': True, 'message': 'Payslip logged successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk=None):
        try:
            slip = MonthlyPayslip.objects.filter(pk=pk).first()
            if not slip:
                return Response({'data': None, 'status': False, 'message': 'Payslip not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = MonthlyPayslipSerializer(slip, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response({'data': MonthlyPayslipSerializer(updated).data, 'status': True, 'message': 'Payslip updated successfully'}, status=status.HTTP_200_OK)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            slip = MonthlyPayslip.objects.filter(pk=pk).first()
            if not slip:
                return Response({'data': None, 'status': False, 'message': 'Payslip not found'}, status=status.HTTP_404_NOT_FOUND)
            slip.delete()
            return Response({'data': None, 'status': True, 'message': 'Payslip deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaxWithholdingSlipView(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                slip = TaxWithholdingSlip.objects.select_related('employment__company', 'document').filter(pk=pk).first()
                if not slip:
                    return Response({'data': None, 'status': False, 'message': 'Withholding tax slip not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer = TaxWithholdingSlipSerializer(slip)
                return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

            tax_slips = TaxWithholdingSlip.objects.select_related('employment__company', 'document').all().order_by('-tax_year')
            employment_id = request.query_params.get('employment_id')
            tax_year = request.query_params.get('tax_year')

            if employment_id:
                tax_slips = tax_slips.filter(employment_id=employment_id)
            if tax_year:
                tax_slips = tax_slips.filter(tax_year=tax_year)

            serializer = TaxWithholdingSlipSerializer(tax_slips, many=True)
            return Response({'data': serializer.data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = TaxWithholdingSlipSerializer(data=request.data)
            if serializer.is_valid():
                slip = serializer.save()
                return Response({'data': TaxWithholdingSlipSerializer(slip).data, 'status': True, 'message': 'Withholding tax slip logged successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk=None):
        try:
            slip = TaxWithholdingSlip.objects.filter(pk=pk).first()
            if not slip:
                return Response({'data': None, 'status': False, 'message': 'Withholding tax slip not found'}, status=status.HTTP_404_NOT_FOUND)

            serializer = TaxWithholdingSlipSerializer(slip, data=request.data, partial=True)
            if serializer.is_valid():
                updated = serializer.save()
                return Response({'data': TaxWithholdingSlipSerializer(updated).data, 'status': True, 'message': 'Withholding tax slip updated successfully'}, status=status.HTTP_200_OK)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            slip = TaxWithholdingSlip.objects.filter(pk=pk).first()
            if not slip:
                return Response({'data': None, 'status': False, 'message': 'Withholding tax slip not found'}, status=status.HTTP_404_NOT_FOUND)
            slip.delete()
            return Response({'data': None, 'status': True, 'message': 'Withholding tax slip deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CareerOverviewView(APIView):
    """
    Returns an aggregated summary for the Career Hub dashboard:
    - Current employment and active client dispatches
    - Chronological career timeline
    - Document counts by category
    - Recent payslips and tax withholding slips
    - Key metrics (total companies, total years of experience, document count, payslip count)
    """
    def get(self, request):
        try:
            employments = (
                Employment.objects.select_related('company')
                .prefetch_related(
                    'dispatch_assignments__dispatched_company',
                    'compensation_history',
                    'documents',
                    'payslips',
                    'tax_slips'
                )
                .all()
                .order_by('-start_date')
            )
            companies = CompanyProfile.objects.all().order_by('name')
            documents = CareerDocument.objects.all()
            payslips = MonthlyPayslip.objects.select_related('employment__company', 'document').all().order_by('-year', '-month')
            tax_slips = TaxWithholdingSlip.objects.select_related('employment__company', 'document').all().order_by('-tax_year')

            current_employment = employments.filter(is_current=True).first()
            active_dispatches = DispatchAssignment.objects.filter(is_current=True).select_related('dispatched_company', 'employment__company')

            # Document category breakdown
            doc_counts = {}
            for doc_type, label in CareerDocument.DOCUMENT_TYPES:
                count = documents.filter(document_type=doc_type).count()
                if count > 0:
                    doc_counts[doc_type] = {'label': label, 'count': count}

            data = {
                'metrics': {
                    'total_companies': companies.count(),
                    'total_employments': employments.count(),
                    'total_documents': documents.count(),
                    'total_payslips': payslips.count(),
                    'total_tax_slips': tax_slips.count(),
                    'active_dispatches_count': active_dispatches.count(),
                    'is_currently_employed': current_employment is not None,
                },
                'current_role': EmploymentSerializer(current_employment).data if current_employment else None,
                'active_dispatches': DispatchAssignmentSerializer(active_dispatches, many=True).data,
                'timeline': EmploymentSerializer(employments, many=True).data,
                'recent_payslips': MonthlyPayslipSerializer(payslips[:6], many=True).data,
                'recent_tax_slips': TaxWithholdingSlipSerializer(tax_slips[:4], many=True).data,
                'document_stats': doc_counts,
                'company_types': [{'id': k, 'label': v} for k, v in CompanyProfile.COMPANY_TYPES],
                'employment_types': [{'id': k, 'label': v} for k, v in Employment.EMPLOYMENT_TYPES],
                'revision_types': [{'id': k, 'label': v} for k, v in CompensationHistory.REVISION_TYPES],
                'salary_frequencies': [{'id': k, 'label': v} for k, v in CompensationHistory.SALARY_FREQUENCIES],
                'document_types': [{'id': k, 'label': v} for k, v in CareerDocument.DOCUMENT_TYPES],
            }
            return Response({'data': data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.core.exceptions import ValidationError
from finance.career.services.payslip_extraction_service import extract_payslip_data
from rest_framework.parsers import MultiPartParser
import json
from django.db import transaction
from finance.career.services.storage_service import upload_payslip_document

class PayslipExtractView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
            
        if file_obj.content_type != 'application/pdf':
            return Response({"error": "Invalid file type. Only PDF is supported."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            pdf_bytes = file_obj.read()
            data = extract_payslip_data(pdf_bytes)
            return Response(data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Extraction failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PayslipSaveView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        data_str = request.data.get('data')
        
        if not file_obj or not data_str:
            return Response({"error": "Missing file or data."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            data = json.loads(data_str)
            employment_id = data.get('employment')
            year = data.get('year')
            month = data.get('month')
            
            employment = Employment.objects.get(id=employment_id, user=request.user)
            
            with transaction.atomic():
                gcs_uri = upload_payslip_document(
                    file_obj=file_obj,
                    user_id=request.user.id,
                    company_slug=employment.company.short_name or employment.company.name,
                    year=int(year),
                    month=int(month),
                    metadata_dict={'filename': file_obj.name}
                )
                
                doc = CareerDocument.objects.create(
                    user=request.user,
                    employment=employment,
                    document_type='payslip_pdf',
                    title=f"{int(year)}-{int(month):02d} Salary Statement",
                    file=gcs_uri,
                    file_name_original=file_obj.name,
                    file_size=file_obj.size,
                    mime_type=file_obj.content_type
                )
                
                payslip = MonthlyPayslip.objects.create(
                    user=request.user,
                    employment=employment,
                    document=doc,
                    year=year,
                    month=month,
                    base_salary=float(data.get('base_salary', 0)),
                    gross_pay=float(data.get('gross_pay', 0)),
                    total_tax=float(data.get('total_tax', 0)),
                    social_insurance_total=float(data.get('social_insurance_total', 0)),
                    total_deductions=float(data.get('total_deductions', 0)),
                    net_pay=float(data.get('net_pay', 0))
                )
                
            return Response({"message": "Payslip saved successfully.", "payslip_id": payslip.id}, status=status.HTTP_201_CREATED)
            
        except Employment.DoesNotExist:
            return Response({"error": "Employment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
