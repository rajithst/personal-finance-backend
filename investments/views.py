import logging

import pandas as pd
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from investments.connector.market_api import MarketApi
from investments.connector.rakuten_sec import BrokerDataLoader
from investments.handlers.forex import ForexHandler, DividendHandler
from investments.handlers.holding import HoldingHandler
from investments.models import StockPurchaseHistory, Company, IndexFundPurchaseHistory, Dividend, Holding
from investments.serializers import StockPurchaseHistorySerializer, CompanySerializer, \
    IndexFundPurchaseHistorySerializer, DividendSerializer, HoldingSerializer, ResponseStockPurchaseHistorySerializer


class InvestmentsView(APIView):

    def get(self, request):
        stock_purchase_history = StockPurchaseHistory.objects.select_related('company')
        index_fund_purchase_history = IndexFundPurchaseHistory.objects.select_related('fund_code').all()
        dividend = Dividend.objects.select_related('company').all()
        holding = Holding.objects.select_related('company').all()
        company = Company.objects.all()

        stock_purchase_history_serializer = ResponseStockPurchaseHistorySerializer(stock_purchase_history, many=True)
        index_fund_purchase_serializer = IndexFundPurchaseHistorySerializer(index_fund_purchase_history, many=True)
        dividend_serializer = DividendSerializer(dividend, many=True)
        holdings_serializer = HoldingSerializer(holding, many=True)
        company_serializer = CompanySerializer(company, many=True)
        dividend_data = pd.DataFrame(dividend_serializer.data)
        us_dividends = dividend_data[dividend_data['stock_currency'] == '$']
        domestic_dividends = dividend_data[dividend_data['stock_currency'] == '¥']
        dividends_us = self._group_by(us_dividends)
        dividends_domestic = self._group_by(domestic_dividends)
        return Response({'companies': company_serializer.data, 'holdings': holdings_serializer.data,
                         'dividends': {
                             'us': dividends_us, 'domestic': dividends_domestic
                         },
                         'transactions': stock_purchase_history_serializer.data}, status=status.HTTP_200_OK)


    def _group_by(self, data: pd.DataFrame):
        if data.empty:
            return []
        # df = pd.DataFrame(data)
        group_data = []
        for group_k, vals in data.groupby(['year', 'month']):
            transactions = vals.to_dict('records')
            group_data.append({'year': group_k[0], 'month': group_k[1], 'month_text': vals['month_text'].iloc[0],
                               'total': vals.amount.sum(), 'transactions': transactions})
        return reversed(group_data)

class StockPurchaseHistoryView(APIView):
    def post(self, request):
        pk = request.data.get('id')
        symbol = request.data.get('company')
        if pk:
            instance = get_object_or_404(StockPurchaseHistory, pk=pk)
            serializer = StockPurchaseHistorySerializer(instance, data=request.data)
        else:
            serializer = StockPurchaseHistorySerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

        HoldingHandler().merge_holding(symbol, update_params=request.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyDataUpdaterView(APIView):

    def get(self, request):
        market_api = MarketApi()
        tickers = ['AAPL', 'AMZN', 'GOOGL', 'ABBV', 'JPM', 'KHC', 'MSFT', 'PG', 'TSM', 'TSLA', 'GASS', '7203.T',
                   '9107.T', '8306.T', '9104.T', '8411.T', '8316.T']
        company_data = market_api.get_company_data(tickers)
        company_serializer = CompanySerializer(data=company_data, many=True)
        if company_serializer.is_valid():
            company_serializer.save()
            return Response(company_serializer.data, status=status.HTTP_201_CREATED)
        return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockDailyUpdaterView(APIView):
    def get(self, request):
        holding_handler = HoldingHandler()
        new_market_data = holding_handler.update_daily_price()
        return Response({'data': new_market_data}, status=status.HTTP_200_OK)


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


class TradeImportView(APIView):
    def get(self, request):
        loader = BrokerDataLoader()
        trades = loader.process()
        purchase_history_serializer = StockPurchaseHistorySerializer(data=trades, many=True)
        if purchase_history_serializer.is_valid(raise_exception=True):
            purchase_history_serializer.save()
        else:
            return Response(purchase_history_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        holdings_handler = HoldingHandler()
        for trade in trades:
            symbol = trade['company']
            holdings_handler.merge_holding(symbol, trade)
        return Response(purchase_history_serializer.data, status=status.HTTP_200_OK)
