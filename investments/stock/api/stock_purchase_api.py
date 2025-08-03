import logging

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.stock.service.holding_service import HoldingService
from investments.stock.service.stock_purchase_service import StockPurchaseService
from investments.validators.portfolio_validator import PortfolioValidator

logger = logging.getLogger(__name__)


class StockPurchaseImportView(APIView):

    def post(self, request):
        upload_files = request.FILES.getlist('files')
        account = request.data.get('account', None)
        portfolio = request.data.get('portfolio', None)
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        target = request.data.get('target', None)

        try:
            logger.info(f"Starting file upload for account {account} and portfolio {portfolio}.")
            upload_parameters = {'upload_files': upload_files, 'account_id': int(account)}
            purchase_service = StockPurchaseService()
            uploaded_files = purchase_service.upload_purchase_files(upload_parameters)
            if not uploaded_files:
                logger.error("File upload failed.")
                return Response({'data': None, 'message': 'Failed to upload files', 'status': False},
                                status=status.HTTP_400_BAD_REQUEST)
            logger.info(f"Files uploaded successfully: {uploaded_files}")
            import_parameters = {
                'target': target,
                'account': int(account),
                'portfolio': int(portfolio),
                'start_date': start_date,
                'end_date': end_date,
                'files': uploaded_files,
            }

            imported_trades = purchase_service.import_purchases(import_parameters)
            if not imported_trades:
                logger.warning("No trades imported from the uploaded files.")
                return Response({'data': None, 'message': 'No trades imported', 'status': False},
                                status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                logger.info("Imported trades: {len(imported_trades)}. Starting bulk purchase creation.")
                purchases_saved, _ = purchase_service.create_bulk_purchase(imported_trades)
                if not purchases_saved:
                    logger.error("Bulk purchase creation failed.")
                    return Response({'data': None, 'message': 'Failed to create bulk purchase', 'status': False},
                                    status=status.HTTP_400_BAD_REQUEST)
                logger.info("Bulk purchase creation successful. Merging holdings.")
                holding_service = HoldingService()
                _ = holding_service.merge_bulk_holdings(imported_trades)
                return Response({'data': imported_trades, 'message': 'Successfully imported trades', 'status': True})

        except Exception as e:
            logger.exception("Error occurred during the stock purchase import process.")
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockPurchaseHistoryView(APIView):
    def get(self, request):
        try:
            PortfolioValidator.validate_request(request.query_params.copy())
            service = StockPurchaseService()
            purchase_history = service.get_purchase_history(request.query_params.copy())
            logger.info("Successfully retrieved purchase history")
            return Response({
                'data': purchase_history, 'message': 'success', 'status': True}, status=status.HTTP_200_OK)
        except ValidationError as e:
            logger.exception(f"Validation error in purchase history request: {e}")
            return Response({
                'data': None, 'message': str(e), 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error retrieving purchase history {e}")
            return Response({
                'data': None, 'message': str(e), 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            with transaction.atomic():
                service = StockPurchaseService()
                is_created, _ = service.create_purchase(request.data.copy())
                if not is_created:
                    logger.warning("Failed to create stock purchase.")
                    return Response({
                        'data': None, 'message': 'Failed to create stock purchase.', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

                holding_service = HoldingService()
                merge_results = holding_service.merge_holding(request.data.copy())
                if not merge_results:
                    logger.error("Holdings merge failed. Rolling back purchase creation.")
                    return Response({
                        'data': None, 'message': 'Holdings merge failed', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

                logger.info("Holdings merged successfully.")
                return Response({
                    'data': merge_results, 'message': 'Holdings merged successfully.', 'status': True},
                    status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception("Error occurred while creating stock purchase.")
            return Response({
                'data': None, 'message': str(e), 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
