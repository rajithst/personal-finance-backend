import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.stock_service import StockService, StockDaemonService
from oauth.permissions import AppEngineCronPermission, AppEngineTaskPermission

logger = logging.getLogger(__name__)

class StocksValueRefreshView(APIView):
    """update daily stock value for all companies in the stock daily price table"""
    permission_classes = [AppEngineTaskPermission]

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

class StocksSplitRefreshView(APIView):
    """ Update daily stock split for all companies in the stock split table"""
    permission_classes = [AppEngineTaskPermission]

    def get(self, request):
        try:
            stock_service = StockService()
            split_data = stock_service.update_daily_stock_split(request.query_params.copy())
            if split_data:
                logger.info("Split data updated successfully.")
                return Response({'data': split_data, 'message': 'success', 'status': True},
                                status=status.HTTP_200_OK)
            logger.warning("Failed to update split data.")
            return Response({'data': split_data, 'message': 'Fail', 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error occurred while importing stock information.")
            return Response({
                'data': None, 'message': str(e), 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StockPriceHistoryView(APIView):
    """get stock price history for a company"""
    def get(self, request):
        try:
            service = StockService()
            stock_price_history = service.get_price_history(request.query_params.copy())
            if stock_price_history is None:
                logger.warning("No price history found")
            logger.info("Successfully fetched stock details for company")
            return Response(
                {'data': stock_price_history or [],
                 'message': 'success', 'status': True
                 },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception("Error occurred while fetching stock details")
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BulkStockValueUpdaterView(APIView):
    """update daily stock value for all companies in the stock daily price table"""
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            service = StockService()
            response = service.sync_historical_data(request.query_params.copy())
            if response:
                logger.info("Successfully synced historical data.")
                return Response({'data': response, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
            logger.warning("Syncing historical data failed for the provided tickers.")
            return Response({'data': response, 'message': 'Failed to sync historical data', 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error occurred while syncing historical stock data.")
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DailyStockValueDaemonView(APIView):
    """ Enqueue task to update daily stock value for all companies in the stock daily price table"""
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            stock_service = StockDaemonService()
            response = stock_service.enqueue_stocks_value_refresh_task(request.query_params.copy())
            return Response({'data': response, 'message': 'success', 'status': True},
                            status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error occurred while importing stock information.")
            return Response({
                'data': None, 'message': str(e), 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailyStockSplitDaemonView(APIView):
    """ Enqueue task to update daily stock split for all companies in the stock split table"""
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            stock_service = StockDaemonService()
            response = stock_service.enqueue_stocks_split_refresh_task(request.query_params.copy())
            return Response({'data': response, 'message': 'success', 'status': True},
                            status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error occurred while importing stock information.")
            return Response({
                'data': None, 'message': str(e), 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

