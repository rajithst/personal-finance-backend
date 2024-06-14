import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.connector.market_api import MarketApi
from investments.handlers.dividend import DividendHandler
from investments.handlers.forex import ForexHandler
from investments.handlers.holding import HoldingHandler
from investments.models import Company, StockDailyPrice, Forex
from investments.serializers.serializers import CompanySerializer


class ForexDailyUpdaterView(APIView):

    def get(self, request):
        symbols = request.GET.get('symbols', None)
        handler = ForexHandler()
        if not symbols:
            forex_symbols = list(Forex.objects.values_list('symbol', flat=True).distinct())
        else:
            forex_symbols = symbols.split(',')
        forex_data = handler.update_forex_data(forex_symbols)
        return Response({'data': forex_data}, status=status.HTTP_200_OK)


class DividendDailyUpdaterView(APIView):

    def get(self, request):
        logging.info('updating dividend data..')
        from_date = request.GET.get('from_date', None)
        to_date = request.GET.get('to_date', None)
        handler = DividendHandler()
        dividend_data = handler.update_dividend_data(from_date, to_date)
        return Response({'data': dividend_data}, status=status.HTTP_200_OK)


class StockDailyUpdaterView(APIView):
    def get(self, request):
        logging.info('updating stock data..')
        tickers = request.GET.get('tickers', None)
        if not tickers:
            tickers = list(Company.objects.values_list('symbol', flat=True))
        else:
            tickers = tickers.split(',')
        holding_handler = HoldingHandler()
        new_market_data = holding_handler.update_daily_price(symbols=tickers)
        return Response({'data': new_market_data}, status=status.HTTP_200_OK)


class HistoricalStockDataUpdaterView(APIView):
    def get(self, request):
        logging.info('updating historical market data..')
        tickers = request.GET.get('tickers', None)
        from_date = request.GET.get('from_date', None)
        to_date = request.GET.get('to_date', None)
        if not tickers:
            tickers = list(Company.objects.values_list('symbol', flat=True))
        else:
            tickers = tickers.split(',')
        market_api = MarketApi()
        historical_data = market_api.get_historical_data(tickers, from_date=from_date, to_date=to_date)
        instances = [StockDailyPrice(**params) for params in historical_data]
        try:
            StockDailyPrice.objects.bulk_create(instances)
            return Response({'data': historical_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.exception('Failed to update historical data')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CompanyDataUpdaterView(APIView):

    def get(self, request):
        tickers = request.GET.get('tickers', None)
        if not tickers:
            raise ValueError('Company tickers not provided')
        tickers = tickers.split(',')
        market_api = MarketApi()
        company_data = market_api.get_company_data(tickers)
        company_serializer = CompanySerializer(data=company_data, many=True)
        if company_serializer.is_valid():
            company_serializer.save()
            return Response(company_serializer.data, status=status.HTTP_201_CREATED)
        return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
