import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.stock.service.holding_service import HoldingService, HoldingDaemonService
from investments.validators.portfolio_validator import PortfolioValidator
from oauth.permissions import AppEngineTaskPermission, AppEngineCronPermission

logger = logging.getLogger(__name__)


class HoldingView(APIView):

    def get(self, request):
        try:
            PortfolioValidator.validate_request(request.query_params.copy())
            service = HoldingService()
            response = service.get_current_holdings(request.query_params.copy())
            return Response({'data': response, 'status': True, 'message': 'success'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            logging.exception('Validation error in holding request', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception('Failed to get holdings', exc_info=e)
            return Response({'data': None, 'status': False, 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HoldingDaemonView(APIView):
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            service = HoldingDaemonService()
            response = service.enqueue_holding_values_refresh_tasks()
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Failed to enqueue holding refresh tasks ')
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HoldingValueRefreshView(APIView):
    permission_classes = [AppEngineTaskPermission]

    def get(self, request):
        try:
            service = HoldingService()
            response = service.refresh_holdings_with_current_price(request.query_params.copy())
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception('Failed to enqueue holding refresh tasks ')
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
