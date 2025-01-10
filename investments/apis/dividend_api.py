import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.dividend_service import DividendService
from oauth.permissions import AppEngineCronPermission


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


class DividendHistoryDaemonView(APIView):
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            task = request.query_params.get('task', None)
            service = DividendService()
            if task == 'pull-dividend-data':
                response = service.update_dividend_history(request.query_params)
            elif task == 'refresh-dividend-payments':
                response = service.enqueue_dividend_refresh_tasks()
            else:
                response = 'Invalid task'
            return Response({'data': response, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.exception('Failed to update dividend payments', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DividendIncomeDaemonView(APIView):
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            service = DividendService()
            response = service.calculate_dividend_payments(request.query_params.copy())
            return Response({'data': response, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.exception('Failed to update dividend payments', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
