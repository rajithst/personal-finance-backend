import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from investments.services.dividend_service import DividendService


class DividendIncomeView(APIView):

    def get(self, request):
        try:
            service = DividendService()
            dividend_incomes = service.get_dividend_income(request.query_params.copy())
            return Response({'data': dividend_incomes, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.exception('Failed to fetch dividend income', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DividendIncomeDaemonView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            service = DividendService()
            service.update_dividend_history(request.query_params)
            response = service.calculate_dividend_payments()
            return Response({'data': response, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.exception('Failed to update dividend payments', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DividendPaymentDaemonView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            service = DividendService()
            service.enqueue_dividend_refresh_tasks()
            return Response({'data': None, 'message': 'Enqueue dividend '}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.exception('Failed to enqueue dividend refresh tasks', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False}, status=status.HTTP_400_BAD_REQUEST)
