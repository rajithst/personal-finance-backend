import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.forex_service import ForexService
from oauth.permissions import AppEngineCronPermission


class DailyForexValueDaemonView(APIView):
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            service = ForexService()
            forex_data = service.update_daily_price(request.query_params.copy())
            return Response({'data': forex_data, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.exception('Failed to update forex prices', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
