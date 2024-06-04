from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.connector.market_api import MarketApi
from investments.handlers.dividend import DividendHandler
from investments.handlers.forex import ForexHandler
from investments.handlers.holding import HoldingHandler
from investments.models import Company
from investments.serializers.serializers import CompanySerializer


class ForexDailyUpdaterView(APIView):

    def get(self, request):
        handler = ForexHandler()
        forex_data = handler.update_forex_data()
        return Response({'data': forex_data}, status=status.HTTP_200_OK)


class DividendDailyUpdaterView(APIView):

    def get(self, request):
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        handler = DividendHandler()
        dividend_data = handler.update_dividend_data(from_date, to_date)
        return Response({'data': dividend_data}, status=status.HTTP_200_OK)


class StockDailyUpdaterView(APIView):
    def get(self, request):
        holding_handler = HoldingHandler()
        new_market_data = holding_handler.update_daily_price()
        return Response({'data': new_market_data}, status=status.HTTP_200_OK)


class CompanyDataUpdaterView(APIView):

    def get(self, request):
        market_api = MarketApi()
        tickers = ['AAPL', 'AMZN', 'GOOGL', 'ABBV', 'JPM', 'KHC', 'MSFT', 'PG', 'TSM', 'TSLA', 'GASS', 'NVDA', '7203.T',
                   '9107.T', '8306.T', '9104.T', '8411.T', '8316.T']
        company_data = market_api.get_company_data(tickers)
        company_serializer = CompanySerializer(data=company_data, many=True)
        if company_serializer.is_valid():
            company_serializer.save()
            return Response(company_serializer.data, status=status.HTTP_201_CREATED)
        return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
