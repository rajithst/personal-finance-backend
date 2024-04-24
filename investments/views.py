from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from investments.connector.market_api import MarketApi
from investments.models import StockPurchaseHistory, Company, IndexFundPurchaseHistory, Dividend
from investments.serializers import StockPurchaseHistorySerializer, CompanySerializer, \
    IndexFundPurchaseHistorySerializer, DividendSerializer


class InvestmentsView(APIView):

    def get(self, request):
        stock_purchase_history = StockPurchaseHistory.objects.select_related('company').all()
        index_fund_purchase_history = IndexFundPurchaseHistory.objects.select_related('fund_code').all()
        dividend = Dividend.objects.select_related('company').all()

        stock_purchase_serializer = StockPurchaseHistorySerializer(stock_purchase_history, many=True)
        index_fund_purchase_serializer = IndexFundPurchaseHistorySerializer(index_fund_purchase_history, many=True)
        dividend_serializer = DividendSerializer(dividend, many=True)
        return Response({'holdings': stock_purchase_serializer.data, 'dividends': dividend_serializer.data}, status=status.HTTP_200_OK)


class StockPurchaseHistoryViewSet(ModelViewSet):
    queryset = StockPurchaseHistory.objects.all()
    serializer_class = StockPurchaseHistorySerializer


class CompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def list(self, request, *args, **kwargs):
        market_api = MarketApi()
        # tickers = ['AAPL', 'AMZN', 'GOOGL', 'ABBV', 'JPM', 'KHC', 'MSFT', 'PG', 'TSM', 'TSLA', 'GASS']
        tickers = ['7203.T', '9107.T', '8306.T', '9104.T', '8411.T', '8316.T']
        company_data = market_api.get_company_data(tickers)
        company_serializer = CompanySerializer(data=company_data, many=True)
        if company_serializer.is_valid():
            company_serializer.save()
            return Response(company_serializer.data, status=status.HTTP_201_CREATED)

        return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
