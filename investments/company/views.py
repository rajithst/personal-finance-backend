import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.company.service.company_service import CompanyService

logger = logging.getLogger(__name__)


class CompanyValueUpdaterView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            service = CompanyService()
            is_success, response = service.fetch_company_info(request.query_params.copy())
            if is_success:
                logger.info("Company information updated successfully.")
                return Response({'data': response, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
            logger.warning("Failed to update company information.")
            return Response({'data': response, 'message': 'Failed to update company information.', 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("Error occurred while importing company information.")
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompanyListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            service = CompanyService()
            response = service.get_company_list()
            return Response({'data': response, 'message': 'success', 'status': True}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Failed to get company list', exc_info=e)
            return Response({'data': None, 'status': False, 'message': 'success'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
