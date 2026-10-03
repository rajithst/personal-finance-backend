from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json
import logging
import os
from datetime import date
from django.conf import settings
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError
from django.db import transaction

logger = logging.getLogger(__name__)

from finance.career.services.payslip_extraction_service import extract_payslip_data, _safe_date_or_none
from finance.career.services.storage_service import (
    upload_payslip_document,
    upload_career_document,
    verify_download_signature,
    open_document_stream,
)

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
                company_slug = 'general'
                employment_id = data.get('employment')
                company_id = data.get('company')
                if employment_id:
                    emp = Employment.objects.filter(id=employment_id, user=request.user).select_related('company').first()
                    if emp and emp.company:
                        company_slug = emp.company.short_name or emp.company.name
                elif company_id:
                    comp = CompanyProfile.objects.filter(id=company_id, user=request.user).first()
                    if comp:
                        company_slug = comp.short_name or comp.name

                doc_type = data.get('document_type', 'other')
                file_uri = upload_career_document(
                    file_obj=file_obj,
                    user_id=request.user.id,
                    company_slug=company_slug,
                    doc_type=doc_type,
                    original_filename=file_obj.name,
                    metadata_dict={'filename': file_obj.name, 'user_id': str(request.user.id)}
                )

                data['file'] = file_uri
                data['file_name_original'] = file_obj.name
                data['file_size'] = file_obj.size
                data['mime_type'] = getattr(file_obj, 'content_type', '') or 'application/pdf'
                if not data.get('title'):
                    data['title'] = file_obj.name

            serializer = CareerDocumentSerializer(data=data)
            if serializer.is_valid():
                doc = serializer.save(user=request.user)
                return Response({'data': CareerDocumentSerializer(doc).data, 'status': True, 'message': 'Document uploaded successfully'}, status=status.HTTP_201_CREATED)
            return Response({'data': serializer.errors, 'status': False, 'message': 'Validation error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            doc = CareerDocument.objects.filter(pk=pk).first()
            if not doc:
                return Response({'data': None, 'status': False, 'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
            if doc.user and request.user.is_authenticated and doc.user != request.user:
                return Response({'data': None, 'status': False, 'message': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            raw_path = str(doc.file.name if hasattr(doc.file, 'name') else doc.file)
            if raw_path.startswith('gs://'):
                try:
                    from google.cloud import storage
                    parts = raw_path.replace('gs://', '').split('/', 1)
                    client = storage.Client()
                    client.bucket(parts[0]).blob(parts[1]).delete()
                except Exception:
                    pass
            elif raw_path.startswith('local://') or raw_path.startswith('local:/'):
                try:
                    clean_path = raw_path.split('local:', 1)[-1].lstrip('/')
                    local_full = os.path.join(settings.MEDIA_ROOT, clean_path)
                    if os.path.exists(local_full):
                        os.remove(local_full)
                except Exception:
                    pass
            elif doc.file:
                try:
                    doc.file.delete(save=False)
                except Exception:
                    pass
            doc.delete()
            return Response({'data': None, 'status': True, 'message': 'Document deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CareerDocumentDownloadView(APIView):
    """
    Streams/downloads career documents from GCS or Local Storage.
    Supports authenticated requests and signed query params (?sig=...).
    """
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        try:
            doc = CareerDocument.objects.filter(pk=pk).first()
            if not doc:
                return Response({'data': None, 'status': False, 'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

            sig = request.query_params.get('sig')
            authorized = False
            if request.user.is_authenticated and doc.user_id == request.user.id:
                authorized = True
            elif sig and verify_download_signature(sig, doc.pk, doc.user_id):
                authorized = True

            if not authorized:
                return Response({'data': None, 'status': False, 'message': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            stream_info = open_document_stream(doc)
            if not stream_info:
                return Response({
                    'data': None,
                    'status': False,
                    'message': 'Document file not found on storage. Please re-upload this document.'
                }, status=status.HTTP_404_NOT_FOUND)

            stream, content_type, filename, size = stream_info
            as_attachment = request.query_params.get('download') == 'true'
            disposition = 'attachment' if as_attachment else 'inline'

            from django.http import FileResponse
            response = FileResponse(stream, content_type=content_type)
            response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
            if size:
                response['Content-Length'] = str(size)
            return response
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
        except (ValidationError, PydanticValidationError) as e:
            logger.warning("Payslip extraction validation error: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Payslip extraction failed: %s", str(e))
            return Response({"error": f"Extraction failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _safe_float(val, default=0.0) -> float:
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _safe_float_or_none(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

class PayslipSaveView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        data_str = request.data.get('data')
        
        if not file_obj or not data_str:
            return Response({"error": "Missing file or data."}, status=status.HTTP_400_BAD_REQUEST)
            
        if file_obj.content_type != 'application/pdf':
            return Response({"error": "Invalid file type. Only PDF is supported."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = json.loads(data_str)
            employment_id = data.get('employment')
            year = int(data.get('year') or 0)
            month = int(data.get('month') or 0)
            is_bonus = bool(data.get('is_bonus', False))

            if not (1900 <= year <= 2100 and 1 <= month <= 12):
                return Response({"error": "Valid year (1900-2100) and month (1-12) are required."}, status=status.HTTP_400_BAD_REQUEST)
            
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
                
                payment_date_val = _safe_date_or_none(data.get('payment_date'), default_year=int(year), default_month=int(month))
                pay_period_start_val = _safe_date_or_none(data.get('pay_period_start'), default_year=int(year), default_month=int(month))
                pay_period_end_val = _safe_date_or_none(data.get('pay_period_end'), default_year=int(year), default_month=int(month))

                doc = CareerDocument.objects.create(
                    user=request.user,
                    employment=employment,
                    document_type='payslip_pdf',
                    title=f"{int(year)}-{int(month):02d} Salary Statement",
                    file=gcs_uri,
                    file_name_original=file_obj.name,
                    file_size=file_obj.size,
                    mime_type=file_obj.content_type,
                    issue_date=payment_date_val or date(int(year), int(month), 1)
                )
                
                payslip_fields = {
                    # Earnings Breakdown
                    'base_salary': _safe_float(data.get('base_salary')),
                    'housing_allowance': _safe_float(data.get('housing_allowance')),
                    'discretionary_allowance': _safe_float(data.get('discretionary_allowance')),
                    'remote_work_allowance': _safe_float(data.get('remote_work_allowance')),
                    'commutation_allowance': _safe_float(data.get('commutation_allowance')),
                    'overtime_pay': _safe_float(data.get('overtime_pay')),
                    'late_night_overtime_pay': _safe_float(data.get('late_night_overtime_pay')),
                    'holiday_work_pay': _safe_float(data.get('holiday_work_pay')),
                    'special_allowance': _safe_float(data.get('special_allowance')),
                    'other_allowances': _safe_float(data.get('other_allowances')),
                    'other_allowances_description': data.get('other_allowances_description') or None,
                    'gross_pay': _safe_float(data.get('gross_pay')),
                    # Social Insurance
                    'health_insurance': _safe_float(data.get('health_insurance')),
                    'nursing_insurance': _safe_float(data.get('nursing_insurance')),
                    'pension': _safe_float(data.get('pension')),
                    'employment_insurance': _safe_float(data.get('employment_insurance')),
                    'social_insurance_total': _safe_float(data.get('social_insurance_total')),
                    # Taxes
                    'taxable_amount': _safe_float_or_none(data.get('taxable_amount')),
                    'income_tax': _safe_float(data.get('income_tax')),
                    'resident_tax': _safe_float(data.get('resident_tax')),
                    'year_end_tax_adjustment': _safe_float(data.get('year_end_tax_adjustment')),
                    'total_tax': _safe_float(data.get('total_tax')),
                    # Other Deductions
                    'union_fee': _safe_float(data.get('union_fee')),
                    'mutual_aid_fee': _safe_float(data.get('mutual_aid_fee')),
                    'meal_deduction': _safe_float(data.get('meal_deduction')),
                    'other_deductions': _safe_float(data.get('other_deductions')),
                    'other_deductions_description': data.get('other_deductions_description') or None,
                    'total_deductions': _safe_float(data.get('total_deductions')),
                    # Net Pay
                    'net_pay': _safe_float(data.get('net_pay')),
                    'bank_transfer_amount': _safe_float_or_none(data.get('bank_transfer_amount')),
                    # Attendance
                    'working_days': _safe_float_or_none(data.get('working_days')),
                    'total_work_hours': _safe_float_or_none(data.get('total_work_hours')),
                    'overtime_hours': _safe_float_or_none(data.get('overtime_hours')),
                    'late_night_hours': _safe_float_or_none(data.get('late_night_hours')),
                    'holiday_work_hours': _safe_float_or_none(data.get('holiday_work_hours')),
                    'absent_days': _safe_float_or_none(data.get('absent_days')),
                    'loss_of_pay_days': _safe_float_or_none(data.get('loss_of_pay_days')),
                    'paid_leave_days_used': _safe_float_or_none(data.get('paid_leave_days_used')),
                    'remaining_paid_leave_days': _safe_float_or_none(data.get('remaining_paid_leave_days')),
                    # Extra metadata & YTD
                    'is_bonus': is_bonus,
                    'payment_date': payment_date_val,
                    'pay_period_start': pay_period_start_val,
                    'pay_period_end': pay_period_end_val,
                    'bank_name': data.get('bank_name') or None,
                    'bank_account': data.get('bank_account') or None,
                    'std_remuneration_health': _safe_float_or_none(data.get('std_remuneration_health')),
                    'std_remuneration_pension': _safe_float_or_none(data.get('std_remuneration_pension')),
                    'ytd_gross_pay': _safe_float_or_none(data.get('ytd_gross_pay')),
                    'ytd_social_insurance': _safe_float_or_none(data.get('ytd_social_insurance')),
                    'ytd_income_tax': _safe_float_or_none(data.get('ytd_income_tax')),
                    'notes': data.get('notes') or None,
                }

                # Check if a payslip for this employment/period already exists or editing by id
                payslip_id = data.get('id')
                payslip = None
                if payslip_id:
                    payslip = MonthlyPayslip.objects.filter(id=payslip_id, user=request.user).first()
                if not payslip:
                    payslip = MonthlyPayslip.objects.filter(
                        employment=employment,
                        year=year,
                        month=month,
                        is_bonus=is_bonus,
                        user=request.user
                    ).first()

                if payslip:
                    payslip.document = doc
                    payslip.year = year
                    payslip.month = month
                    for key, val in payslip_fields.items():
                        setattr(payslip, key, val)
                    payslip.save()
                else:
                    payslip = MonthlyPayslip.objects.create(
                        user=request.user,
                        employment=employment,
                        document=doc,
                        year=year,
                        month=month,
                        **payslip_fields
                    )
                
            return Response({"message": "Payslip saved successfully.", "payslip_id": payslip.id}, status=status.HTTP_201_CREATED)
            
        except Employment.DoesNotExist:
            return Response({"error": "Employment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PayslipAnalyticsView(APIView):
    """
    Dedicated analytical aggregation endpoint for MonthlyPayslip records.
    Provides multi-year summary metrics, YoY comparisons, monthly Recharts points,
    and deduction friction composition.
    """
    def get(self, request):
        try:
            user = request.user
            queryset = MonthlyPayslip.objects.filter(user=user).select_related('employment__company')

            # Optional query filters
            company_id = request.query_params.get('company_id')
            if company_id:
                try:
                    queryset = queryset.filter(employment__company_id=int(company_id))
                except (ValueError, TypeError):
                    pass

            year = request.query_params.get('year')
            if year:
                try:
                    queryset = queryset.filter(year=int(year))
                except (ValueError, TypeError):
                    pass

            include_bonus = request.query_params.get('include_bonus')
            if include_bonus is not None and include_bonus.lower() in ('false', '0', 'no'):
                queryset = queryset.filter(is_bonus=False)

            payslips = list(queryset.order_by('year', 'month', 'is_bonus', 'id'))

            total_gross = sum(float(p.gross_pay or 0) for p in payslips)
            total_net = sum(float(p.net_pay or 0) for p in payslips)
            total_pension_employee = sum(float(p.pension or 0) for p in payslips)
            total_pension_system = total_pension_employee * 2.0  # Japan 50/50 statutory match
            total_health = sum(float(p.health_insurance or 0) for p in payslips)
            total_emp_ins = sum(float(p.employment_insurance or 0) for p in payslips)
            total_social = sum(float(p.social_insurance_total or 0) for p in payslips)
            total_income_tax = sum(float(p.income_tax or 0) for p in payslips)
            total_resident_tax = sum(float(p.resident_tax or 0) for p in payslips)
            total_tax = sum(float(p.total_tax or 0) for p in payslips)
            total_year_end_adj = sum(float(p.year_end_tax_adjustment or 0) for p in payslips)
            total_other_ded = sum(float(p.other_deductions or 0) for p in payslips)
            total_deductions = sum(float(p.total_deductions or 0) for p in payslips)
            count = len(payslips)

            take_home_ratio = round((total_net / total_gross * 100), 1) if total_gross > 0 else 0.0
            tax_ratio = round((total_tax / total_gross * 100), 1) if total_gross > 0 else 0.0
            social_ratio = round((total_social / total_gross * 100), 1) if total_gross > 0 else 0.0
            deduction_ratio = round((total_deductions / total_gross * 100), 1) if total_gross > 0 else 0.0

            summary = {
                'total_gross_pay': total_gross,
                'total_net_pay': total_net,
                'total_social_insurance': total_social,
                'total_pension_employee': total_pension_employee,
                'total_pension_system_contribution': total_pension_system,
                'total_health_insurance': total_health,
                'total_employment_insurance': total_emp_ins,
                'total_income_tax': total_income_tax,
                'total_resident_tax': total_resident_tax,
                'total_taxes': total_tax,
                'total_year_end_adjustment': total_year_end_adj,
                'total_other_deductions': total_other_ded,
                'total_deductions': total_deductions,
                'overall_take_home_ratio': take_home_ratio,
                'overall_tax_ratio': tax_ratio,
                'overall_social_ratio': social_ratio,
                'overall_deduction_ratio': deduction_ratio,
                'payslips_count': count,
            }

            # Monthly timeline
            monthly_timeline = []
            for p in payslips:
                gross = float(p.gross_pay or 0)
                net = float(p.net_pay or 0)
                co_id = p.employment.company_id if p.employment else None
                co_name = p.employment.company.name if (p.employment and p.employment.company) else "Unknown"
                monthly_timeline.append({
                    'year_month': f"{p.year}-{p.month:02d}" + (" (Bonus)" if p.is_bonus else ""),
                    'year': p.year,
                    'month': p.month,
                    'is_bonus': p.is_bonus,
                    'company_id': co_id,
                    'company_name': co_name,
                    'gross_pay': gross,
                    'net_pay': net,
                    'pension': float(p.pension or 0),
                    'health_insurance': float(p.health_insurance or 0),
                    'employment_insurance': float(p.employment_insurance or 0),
                    'social_insurance_total': float(p.social_insurance_total or 0),
                    'income_tax': float(p.income_tax or 0),
                    'resident_tax': float(p.resident_tax or 0),
                    'total_tax': float(p.total_tax or 0),
                    'total_deductions': float(p.total_deductions or 0),
                    'take_home_ratio': round((net / gross * 100), 1) if gross > 0 else 0.0,
                    'std_remuneration_pension': float(p.std_remuneration_pension) if p.std_remuneration_pension is not None else None,
                    'std_remuneration_health': float(p.std_remuneration_health) if p.std_remuneration_health is not None else None,
                })

            # Yearly comparisons
            years_dict = {}
            for p in payslips:
                yr = p.year
                if yr not in years_dict:
                    years_dict[yr] = []
                years_dict[yr].append(p)

            sorted_years = sorted(years_dict.keys())
            yearly_comparisons = []
            prev_gross = None
            prev_net = None

            for yr in sorted_years:
                yr_slips = years_dict[yr]
                y_gross = sum(float(x.gross_pay or 0) for x in yr_slips)
                y_net = sum(float(x.net_pay or 0) for x in yr_slips)
                y_pension = sum(float(x.pension or 0) for x in yr_slips)
                y_health = sum(float(x.health_insurance or 0) for x in yr_slips)
                y_social = sum(float(x.social_insurance_total or 0) for x in yr_slips)
                y_income_tax = sum(float(x.income_tax or 0) for x in yr_slips)
                y_resident_tax = sum(float(x.resident_tax or 0) for x in yr_slips)
                y_total_tax = sum(float(x.total_tax or 0) for x in yr_slips)
                y_deductions = sum(float(x.total_deductions or 0) for x in yr_slips)
                y_take_home_ratio = round((y_net / y_gross * 100), 1) if y_gross > 0 else 0.0

                yoy_gross = round(((y_gross - prev_gross) / prev_gross * 100), 1) if (prev_gross is not None and prev_gross > 0) else None
                yoy_net = round(((y_net - prev_net) / prev_net * 100), 1) if (prev_net is not None and prev_net > 0) else None

                prev_gross = y_gross
                prev_net = y_net

                yearly_comparisons.append({
                    'year': yr,
                    'gross_pay': y_gross,
                    'net_pay': y_net,
                    'pension': y_pension,
                    'health_insurance': y_health,
                    'social_insurance_total': y_social,
                    'income_tax': y_income_tax,
                    'resident_tax': y_resident_tax,
                    'total_tax': y_total_tax,
                    'total_deductions': y_deductions,
                    'take_home_ratio': y_take_home_ratio,
                    'yoy_gross_growth_pct': yoy_gross,
                    'yoy_net_growth_pct': yoy_net,
                })

            # Deduction composition
            deduction_composition = []
            if total_deductions > 0:
                raw_items = [
                    ('Welfare Pension (厚生年金)', total_pension_employee, '#6366f1'),
                    ('Health Insurance (健康保険)', total_health, '#06b6d4'),
                    ('Employment Insurance (雇用保険)', total_emp_ins, '#3b82f6'),
                    ('National Income Tax (所得税)', total_income_tax, '#ef4444'),
                    ('Resident Tax (住民税)', total_resident_tax, '#f59e0b'),
                    ('Other / Mutual Aid Deductions', total_other_ded, '#8b5cf6'),
                ]
                for name, amount, color in raw_items:
                    if amount > 0:
                        pct = round((amount / total_deductions * 100), 1)
                        deduction_composition.append({
                            'name': name,
                            'amount': amount,
                            'percentage': pct,
                            'color': color,
                        })

            data = {
                'summary': summary,
                'yearly_comparisons': yearly_comparisons,
                'monthly_timeline': monthly_timeline,
                'deduction_composition': deduction_composition,
            }
            return Response({'data': data, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Failed to compute payslip analytics")
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

