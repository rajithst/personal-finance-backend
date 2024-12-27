import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.stock_service import StockService

logger = logging.getLogger(__name__)


class DailyStockValueDaemonView(APIView):

    def get(self, request):
        try:
            stock_service = StockService()
            new_market_data = stock_service.update_daily_price(request.query_params.copy())
            if new_market_data:
                logger.info("Stock value updated successfully.")
                return Response({'data': new_market_data, 'message': 'success', 'status': True},
                                status=status.HTTP_200_OK)
            logger.warning("Failed to update stock value.")
            return Response({'data': new_market_data, 'message': 'Fail', 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error occurred while importing stock information.")
            return Response({
                'data': None, 'message': str(e), 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockPriceHistoryView(APIView):

    def get(self, request):
        try:
            service = StockService()
            stock_price_history = service.get_price_history(request.query_params.copy())
            if stock_price_history is None:
                logger.warning(f"No price history found")
            logger.info(f"Successfully fetched stock details for company")
            return Response(
                {'data': stock_price_history or [],
                 'message': 'success', 'status': True
                 },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception(f"Error occurred while fetching stock details")
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkStockValueUpdaterView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            service = StockService()
            response = service.sync_historical_data(request.query_params.copy())
            if response:
                logger.info(f"Successfully synced historical data.")
                return Response({'data': response, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
            logger.warning("Syncing historical data failed for the provided tickers.")
            return Response({'data': response, 'message': 'Failed to sync historical data', 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error occurred while syncing historical stock data.")
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
