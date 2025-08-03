from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.settings.service.settings_service import SettingsService


class ClientSettingsView(APIView):
    def get(self, request):
        try:
            service = SettingsService()
            broker_accounts = service.get_broker_accounts()
            portfolios = service.get_portfolios()
            return Response({'data': {
                'broker_accounts': broker_accounts,
                'portfolios': portfolios
            }, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
