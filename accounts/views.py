from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.service.account_service import CreditAccountService


class CreditAccountView(APIView):

    def post(self, request):
        try:
            service = CreditAccountService()
            account = service.create_account(request.data)
            return Response({'data': account, 'status': True, 'message': 'Success'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            service = CreditAccountService()
            account = service.update_account(request.data)
            return Response({'data': account, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
