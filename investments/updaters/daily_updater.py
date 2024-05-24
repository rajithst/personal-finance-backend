from rest_framework import status
from rest_framework.views import APIView

from investments.handlers.holding import HoldingHandler
from rest_framework.response import Response


class StockDailyUpdaterView(APIView):
    def get(self, request):
        holding_handler = HoldingHandler()
        new_market_data = holding_handler.update_daily_price()
        return Response({'data': new_market_data}, status=status.HTTP_200_OK)