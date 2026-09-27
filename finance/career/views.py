from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from finance.career.services.payslip_extraction_service import extract_payslip_data
from rest_framework.parsers import MultiPartParser

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

import json
from django.db import transaction
from finance.career.models import CareerDocument, MonthlyPayslip, Employment
from finance.career.services.storage_service import upload_payslip_document

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
