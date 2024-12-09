import logging

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.holding_service import HoldingService
from investments.services.stock_purchase_service import StockPurchaseService
from investments.services.stock_service import StockService

logger = logging.getLogger(__name__)


class DailyStockValueUpdateView(APIView):

    def get(self, request):
        logger.info('Updating stock data...')
        query_params = request.query_params
        company = query_params.get('company', None)
        if not company:
            logger.error('Company parameter is missing.')
            return Response({'error': 'company is required'}, status=status.HTTP_400_BAD_REQUEST)
        companies = company.split(',')

        try:
            stock_service = StockService()
            new_market_data = stock_service.update_daily_price(companies)
        except Exception as e:
            logger.exception("Error occurred while importing stock information.")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if new_market_data:
            logger.info("Stock value updated successfully.")
            return Response(new_market_data, status=status.HTTP_200_OK)

        logger.warning("Failed to update stock value.")
        return Response(new_market_data, status=status.HTTP_400_BAD_REQUEST)


class StockPurchaseHistoryView(APIView):
    def get(self, request):
        try:
            purchase_params = {
                'company': request.query_params.get('company', None),
                'portfolio': request.query_params.get('portfolio', None),
                'start_date': request.query_params.get('start_date', None),
                'end_date': request.query_params.get('end_date', None),
            }
            service = StockPurchaseService()
            purchase_history = service.get_purchase_history(purchase_params)
            logger.info(f"Successfully retrieved purchase history")
            return Response(purchase_history, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error retrieving purchase history")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        data = request.data
        if not data:
            logger.error("No data provided in POST request.")
            raise ValidationError({'error': 'Purchase data is required'})
        try:
            with transaction.atomic():
                service = StockPurchaseService()
                is_created, response = service.create_purchase(data)
                if not is_created:
                    logger.warning("Failed to create stock purchase.")
                    return Response({'error': response}, status=status.HTTP_400_BAD_REQUEST)

                holding_service = HoldingService()
                merge_results = holding_service.merge_holding(data)
                if not merge_results:
                    logger.error("Holdings merge failed. Rolling back purchase creation.")
                    raise Exception("Failed to merge holdings after purchase creation.")

                logger.info("Holdings merged successfully.")
                return Response({'data': merge_results}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception("Error occurred while creating stock purchase.")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockDetailView(APIView):

    def get(self, request):
        company = request.query_params.get('company')
        if not company:
            logger.error("Company parameter is missing in GET request.")
            return Response({'error': 'Company is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.info(f"Fetching stock details for company: {company}")
            service = StockService()
            purchase_service = StockPurchaseService()
            stock_price_history = service.get_price_history(company)
            stock_purchase_history = purchase_service.get_purchase_history(company)
            if stock_price_history is None:
                logger.warning(f"No price history found for company: {company}")
            if stock_purchase_history is None:
                logger.warning(f"No purchase history found for company: {company}")

            logger.info(f"Successfully fetched stock details for company: {company}")
            return Response(
                {
                    'prices': stock_price_history or [],
                    'purchase_history': stock_purchase_history or [],
                    'company': company,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception(f"Error occurred while fetching stock details for company: {company}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkStockValueUpdaterView(APIView):
    def get(self, request):
        tickers = request.query_params.get('tickers')
        if not tickers:
            logger.error("Tickers parameter is missing in GET request.")
            return Response({'error': 'Tickers are required'}, status=status.HTTP_400_BAD_REQUEST)

        tickers_list = tickers.split(',')
        if not tickers_list or any(not ticker.strip() for ticker in tickers_list):
            logger.error("Invalid tickers list provided.")
            raise ValidationError({'error': 'Tickers list is invalid or contains empty values.'})
        try:
            service = StockService()
            response = service.sync_historical_data({'tickers': tickers_list})
            if response:
                logger.info(f"Successfully synced historical data for tickers: {tickers_list}.")
                return Response(response, status=status.HTTP_200_OK)
            logger.warning("Syncing historical data failed for the provided tickers.")
            return Response({'error': 'Failed to update stock values'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error occurred while syncing historical stock data.")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                return Response({'message': 'Failed to upload files', 'status': False},
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
                return Response({'message': 'No trades imported', 'status': False}, status=status.HTTP_400_BAD_REQUEST)

            failed_merges = []
            with transaction.atomic():
                logger.info(f"Imported trades: {len(imported_trades)}. Starting bulk purchase creation.")
                purchases_saved, response = purchase_service.create_bulk_purchase(imported_trades)

                if not purchases_saved:
                    logger.error("Bulk purchase creation failed.")
                    return Response({'message': 'Failed to save purchases', 'status': False},
                                    status=status.HTTP_400_BAD_REQUEST)

                logger.info("Bulk purchase creation successful. Merging holdings.")
                holding_service = HoldingService()

                for trade in imported_trades:
                    if not holding_service.merge_holding(trade):
                        failed_merges.append(trade)

            if failed_merges:
                logger.warning(f"Holdings merge failed for {len(failed_merges)} trades.")
                return Response(
                    {
                        'message': 'Partially imported: Some holdings could not be merged.',
                        'failed_trades': failed_merges,
                        'status': True,
                    },
                    status=status.HTTP_207_MULTI_STATUS,
                )
            return Response({'message': 'Successfully imported trades', 'status': True})


        except Exception as e:
            logger.exception("Error occurred during the stock purchase import process.")
            return Response({'message': str(e), 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
