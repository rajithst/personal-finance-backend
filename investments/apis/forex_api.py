import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.forex_service import ForexService
from oauth.permissions import AppEngineCronPermission


class DailyForexValueDaemonView(APIView):
    permission_classes = [AppEngineCronPermission]
    def get(self, request):
        logging.info('updating forex data..')
        query_params = request.query_params
        currency = query_params.get('currency', None)
        if not currency:
            return Response({'error': 'currency is required'}, status=status.HTTP_400_BAD_REQUEST)
        currencies = currency.split(',')
        service = ForexService()
        forex_data = service.update_daily_price(currencies)
        return Response({'data': forex_data}, status=status.HTTP_200_OK)