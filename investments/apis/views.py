from datetime import date

import pandas as pd
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets

from investments.handlers.holding import HoldingHandler
from investments.models import StockPurchaseHistory, Company, Dividend, Holding, StockDailyPrice
from investments.serializers.response_serializers import ResponseStockPurchaseHistorySerializer, \
    ResponseDividendSerializer, ResponseHoldingSerializer
from investments.serializers.serializers import CompanySerializer, StockPurchaseHistorySerializer, DividendSerializer, \
    HoldingSerializer, StockDailyPriceSerializer


class InvestmentsView(APIView):

    def get(self, request):
        stock_purchase_history = StockPurchaseHistory.objects.select_related('company')
        dividend = Dividend.objects.select_related('company').all()
        holding = Holding.objects.select_related('company').all()
        company = Company.objects.all()

        stock_purchase_history_serializer = ResponseStockPurchaseHistorySerializer(stock_purchase_history, many=True)
        stock_purchase_history_data = stock_purchase_history_serializer.data

        dividend_serializer = ResponseDividendSerializer(dividend, many=True)
        holdings_serializer = ResponseHoldingSerializer(holding, many=True)
        company_serializer = CompanySerializer(company, many=True)

        dividend_data = dividend_serializer.data
        us_dividends_calculated = domestic_dividends_calculated = []
        if dividend_data:
            dividend_data = pd.DataFrame(dividend_serializer.data)
            us_dividends = dividend_data[dividend_data['stock_currency'] == '$']
            domestic_dividends = dividend_data[dividend_data['stock_currency'] == '¥']
            dividends_us = self._group_by(us_dividends)
            dividends_domestic = self._group_by(domestic_dividends)
            us_dividends_calculated = self.calculate_monthly_dividends(dividends_us, stock_purchase_history_data)
            domestic_dividends_calculated = self.calculate_monthly_dividends(dividends_domestic,
                                                                             stock_purchase_history_data)
        return Response({'companies': company_serializer.data, 'holdings': holdings_serializer.data,
                         'dividends': {
                             'us': us_dividends_calculated, 'domestic': domestic_dividends_calculated
                         },
                         'transactions': stock_purchase_history_serializer.data}, status=status.HTTP_200_OK)

    def calculate_monthly_dividends(self, dividends, stock_purchase_history):
        dividends_calculated = []
        stock_purchase_history_df = pd.DataFrame(stock_purchase_history)
        for dv in dividends:
            obj = {'year': dv.get('year'), 'month': dv.get('month'), 'month_text': dv.get('month_text'), 'total': 0}
            dividend_payers = dv.get('transactions')
            adjusted_transactions = []
            total_payment = 0
            currency = ''
            for payer in dividend_payers:
                ticker = payer.get('company')
                ex_dividend_date = payer.get('ex_dividend_date')
                currency = payer.get('stock_currency')
                filtered_df = stock_purchase_history_df[(stock_purchase_history_df['company'] == ticker) & (
                        stock_purchase_history_df['purchase_date'] < ex_dividend_date)]
                eligible_quantity = filtered_df['quantity'].sum()
                if eligible_quantity:
                    payer['quantity'] = eligible_quantity
                    payer['total_amount'] = eligible_quantity * float(payer.get('amount'))
                    total_payment += payer['total_amount']
                    adjusted_transactions.append(payer)
            if adjusted_transactions:
                obj['total'] = total_payment
                obj['currency'] = currency
                obj['transactions'] = adjusted_transactions
                dividends_calculated.append(obj)
        return dividends_calculated

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


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class StockDailyPriceView(APIView):

    def get_object(self, company_id):
        try:
            start_date = date(2024, 1, 1)
            end_date = date(2024, 12, 31)
            return StockDailyPrice.objects.filter(company_id=company_id, date__range=(start_date, end_date)).order_by('date')
        except StockDailyPrice.DoesNotExist:
            raise Http404

    def get(self, request, symbol):
        stocks = self.get_object(symbol)
        serializer = StockDailyPriceSerializer(stocks, many=True)
        return Response({'prices': serializer.data, 'symbol': symbol})
