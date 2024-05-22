from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.connector.rakuten_sec import BrokerDataLoader
from investments.handlers.holding import HoldingHandler
from investments.serializers.serializers import StockPurchaseHistorySerializer


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