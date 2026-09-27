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
