from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.settings.service.settings_service import SettingsService


class ClientSettings(APIView):

    def get(self, request):

        try:
            service = SettingsService()
            accounts = service.get_credit_accounts()
            transaction_categories = service.get_transaction_categories()
            transaction_subcategories = service.get_transaction_subcategories()
            account_types = service.get_account_types()
            account_providers = service.get_account_providers()
            return Response({'data': {
                'accounts': accounts,
                'account_types': account_types,
                'account_providers': account_providers,
                'transaction_categories': transaction_categories,
                'transaction_subcategories': transaction_subcategories
            }, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
