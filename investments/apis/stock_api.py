import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.stock_import_service import StockImportService
from investments.services.stock_service import StockService
from utils.uploader import FileUploadService


class DailyStockValueUpdateView(APIView):
    def get(self, request):
        logging.info('updating stock data..')
        query_params = request.query_params
        company = query_params.get('company', None)
        if not company:
            return Response({'error': 'company is required'}, status=status.HTTP_400_BAD_REQUEST)
        companies = company.split(',')
        stock_service = StockService()
        new_market_data = stock_service.update_daily_price(companies)
        return Response({'data': new_market_data}, status=status.HTTP_200_OK)


class StockPurchaseHistoryView(APIView):
    def get(self, request):
        query_params = request.query_params
        company = query_params.get('company', None)
        service = StockService()
        purchase_history = service.get_purchase_history(company)
        return Response({'data': purchase_history}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        service = StockService()
        is_created, response = service.create_purchase(data)
        if is_created:
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class StockDetailView(APIView):

    def get(self, request):
        query_params = request.query_params
        company = query_params.get('company', None)
        if not company:
            return Response({'error': 'company is required'}, status=status.HTTP_400_BAD_REQUEST)
        service = StockService()
        stock_price_history = service.get_price_history(company)
        stock_purchase_history = service.get_purchase_history(company)
        return Response({'prices': stock_price_history, 'purchase_history': stock_purchase_history, 'company': company},
                        status=status.HTTP_200_OK)


class BulkStockValueUpdaterView(APIView):
    def get(self, request):
        query_params = request.query_params
        tickers = query_params.get('tickers', None)
        if not tickers:
            return Response({'error': 'tickers is required'}, status=status.HTTP_400_BAD_REQUEST)
        service = StockService()
        response = service.import_historical_data(query_params)
        if response:
            return Response(response, status=status.HTTP_200_OK)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class StockPurchaseImportView(APIView):
    def get(self, request):
        pass
        # file_name = self.request.get('file_name', None)
        # loader = BrokerDataLoader()
        # trades = loader.process()
        # purchase_history_serializer = StockPurchaseHistorySerializer(data=trades, many=True)
        # if purchase_history_serializer.is_valid(raise_exception=True):
        #     purchase_history_serializer.save()
        # else:
        #     return Response(purchase_history_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # holdings_handler = HoldingHandler()
        # for trade in trades:
        #     symbol = trade['company']
        #     holdings_handler.merge_holding(symbol, trade)
        # return Response(purchase_history_serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
        upload_files = request.FILES.getlist('files')
        account_id = request.data.get('account_id', None)
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        if not account_id:
            return Response({'message': 'Account must be selected', 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        if not upload_files:
            return Response({'message': 'No files uploaded', 'status': False}, status=status.HTTP_400_BAD_REQUEST)

        account_id = int(account_id)
        upload_parameters = {
            'upload_files': upload_files,
            'account_id': account_id,
        }
        upload_service = FileUploadService()
        uploaded_files = upload_service.upload_trade_files(upload_parameters)
        if not uploaded_files:
            return Response({'message': 'Failed to upload files', 'status': False}, status=status.HTTP_400_BAD_REQUEST)

        failed_uploads = [file for file in uploaded_files if file not in upload_files]
        import_parameters = {
            'account_id': account_id,
            'start_date': start_date,
            'end_date': end_date,
            'files': uploaded_files,
        }

        import_service = StockImportService()
        imported_trades = import_service.import_trades(import_parameters)
        if imported_trades:
            stock_service = StockService()
            is_purchased_created, response = stock_service.create_bulk_purchase(imported_trades)
            if is_purchased_created:
                for trade in imported_trades:
                    company = trade['company']
                    stock_service.merge_holding(company, trade)