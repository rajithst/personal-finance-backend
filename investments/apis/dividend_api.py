import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.dividend_service import DividendService


class DividendIncomeView(APIView):

    def get(self, request):
        service = DividendService()
        dividend_incomes = service.get_dividend_income()
        return Response({'dividend_incomes': dividend_incomes}, status=status.HTTP_200_OK)


class DividendPaymentView(APIView):

    def get(self, request):
        logging.info('calculating dividend payments..')
        ticker = request.query_params.get('ticker')
        if ticker is None:
            return Response({'message': 'Company ticker is required'}, status=status.HTTP_400_BAD_REQUEST)
        service = DividendService()
        service.calculate_dividend_payments()
        return Response({'message': 'Task created'}, status=status.HTTP_200_OK)


class DividendImporterView(APIView):

    def get(self, request):
        logging.info('import dividend data..')
        service = DividendService()
        service.import_dividends()
        return Response({'message': 'Task created'}, status=status.HTTP_200_OK)
