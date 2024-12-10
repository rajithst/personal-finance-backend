import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from investments.services.dividend_service import DividendService


class DividendIncomeView(APIView):

    def get(self, request):
        service = DividendService()
        dividend_incomes = service.get_dividend_income()
        return Response(dividend_incomes, status=status.HTTP_200_OK)


class DividendPaymentUpdaterView(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):
        logging.info('updating dividend payments..')
        service = DividendService()
        service.update_dividend_history(request.query_params)
        response = service.calculate_dividend_payments()
        return Response({'dividend_payments': response}, status=status.HTTP_200_OK)


class DividendImporterView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logging.info('import dividend data..')
        service = DividendService()
        service.enqueue_dividend_refresh_tasks()
        return Response({'message': 'Task created'}, status=status.HTTP_200_OK)
