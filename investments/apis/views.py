import logging

import pandas as pd
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets

from investments.handlers.holding import HoldingHandler
from investments.models import StockPurchaseHistory, Company, Dividend, Holding
from investments.serializers.response_serializers import ResponseStockPurchaseHistorySerializer, \
    ResponseDividendSerializer, ResponseHoldingSerializer
from investments.serializers.serializers import CompanySerializer, StockPurchaseHistorySerializer, DividendSerializer, \
    HoldingSerializer


class InvestmentsView(APIView):

    def get(self, request):
        stock_purchase_history = StockPurchaseHistory.objects.select_related('company')
        dividend = Dividend.objects.select_related('company').all()
        holding = Holding.objects.select_related('company').all()
        company = Company.objects.all()

        stock_purchase_history_serializer = ResponseStockPurchaseHistorySerializer(stock_purchase_history, many=True)
        dividend_serializer = ResponseDividendSerializer(dividend, many=True)
        holdings_serializer = ResponseHoldingSerializer(holding, many=True)
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


class StockPurchaseHistoryViewSet(viewsets.ModelViewSet):
    queryset = StockPurchaseHistory.objects.all()
    serializer_class = StockPurchaseHistorySerializer

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


class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer


class HoldingViewSet(viewsets.ModelViewSet):
    queryset = Holding.objects.all()
    serializer_class = HoldingSerializer

    def post(self, request):
        pk = request.data.get('id')
        symbol = request.data.get('company')
        if pk:
            instance = get_object_or_404(StockPurchaseHistory, pk=pk)
            serializer = HoldingSerializer(instance, data=request.data)
        else:
            serializer = HoldingSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

        HoldingHandler().merge_holding(symbol, update_params=request.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompanyViewSet(viewsets.ViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
