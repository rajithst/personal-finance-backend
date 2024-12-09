import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.company_service import CompanyService

logger = logging.getLogger(__name__)


class CompanyValueUpdaterView(APIView):
    """
    API View to update company values based on tickers.

    Attributes:
        permission_classes (list): List of permissions for the API endpoint.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        Handles GET requests to update company information.

        Args:
            request: DRF request object.

        Returns:
            Response: DRF Response with status and data.

        Raises:
            ValidationError: If `tickers` parameter is missing or invalid.
        """
        query_params = request.query_params
        tickers = query_params.get('tickers', None)
        if not tickers:
            logger.error("Tickers parameter missing in request.")
            raise ValidationError({'error': 'Company tickers not provided'})
        tickers = tickers.split(',')
        request_data = {
            'tickers': tickers
        }
        try:
            service = CompanyService()
            is_success, response = service.import_company_information(request_data)
        except Exception as e:
            logger.exception("Error occurred while importing company information.")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if is_success:
            logger.info("Company information updated successfully.")
            return Response(response, status=status.HTTP_200_OK)

        logger.warning("Failed to update company information.")
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
