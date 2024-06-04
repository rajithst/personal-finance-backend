from rest_framework import status
from rest_framework.views import APIView
#
# from investments.handlers.forex import DividendHandler
# from investments.handlers.holding import HoldingHandler
# from rest_framework.response import Response


# class StockDailyUpdaterView(APIView):
#     def get(self, request):
#         holding_handler = HoldingHandler()
#         new_market_data = holding_handler.update_daily_price()
#         return Response({'data': new_market_data}, status=status.HTTP_200_OK)
#
#
# class DividendDailyUpdaterView(APIView):
#     def get(self, request):
#         for dv in dividends_us:
#             dividend_payers = dv.get('transactions')
#             for payer in dividend_payers:
#                 ticker = payer.get('company')
#                 ex_dividend_date = payer.get('ex_dividend_date')
#                 eligible_quantity = \
#                 stock_purchase_history.filter(company_id=ticker, purchase_date__lt=ex_dividend_date).aggregate(
#                     total_quantity=Sum('quantity'))['quantity']
