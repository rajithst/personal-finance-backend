import logging

from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.transactions.services.transaction_import_service import TransactionImportService
from finance.transactions.services.transaction_list_service import TransactionListService, TransactionBulkService


class TransactionView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            id = kwargs.get('id')
            if id:
                transaction_id = int(id)
                list_service = TransactionListService()
                transaction = list_service.get_transaction_by_id(transaction_id)
                if transaction:
                    return Response({'data': transaction, 'status': True, 'message': 'Success'},
                                    status=status.HTTP_200_OK)
                return Response({'data': None, 'status': False, 'message': 'Transaction not found'},
                                status=status.HTTP_404_NOT_FOUND)
            else:
                list_service = TransactionListService()
                transactions = list_service.get_transactions(request.query_params.copy())
                return Response({'data': transactions, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            update_similar = data.get('update_similar')
            list_service = TransactionListService()
            if update_similar:
                list_service.update_similar_transactions(data)
            created, response = list_service.create_transaction(data)
            if created:
                return Response({'data': response, 'status': True, 'message': 'Success'},
                                status=status.HTTP_201_CREATED)
            return Response({'data': None, 'status': False, 'message': 'Transaction not created'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            update_similar = data.get('update_similar')
            merge_ids = data.get('merge_ids')
            list_service = TransactionListService()
            if merge_ids:
                list_service.merge_transactions(data)
            if update_similar:
                list_service.update_similar_transactions(data)

            updated, response = list_service.update_transaction(data)
            if updated:
                return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
            return Response({'data': None, 'status': False, 'message': 'Transaction not updated'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionBulkView(APIView):
    def put(self, request):
        try:
            data = request.data
            task = data.get('task')
            bulk_service = TransactionBulkService()
            is_success = False
            response = None
            if task == 'delete':
                is_success, response = bulk_service.bulk_delete(data)
            elif task == 'split':
                is_success, response = bulk_service.split_transactions(data)

            if is_success:
                return Response({
                    'data': response, 'status': True, 'message': 'Success'
                }, status=status.HTTP_200_OK)
            return Response({
                'data': response, 'status': False, 'message': 'Failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionImportView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request):
        upload_files = request.FILES.getlist('files')
        account_id = request.data.get('account_id', None)
        drop_duplicates = request.data.get('drop_duplicates', True)
        import_from_last_date = request.data.get('import_from_last_date', False)
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        if not account_id:
            return Response({'data': None, 'message': 'Account must be selected', 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        if not upload_files:
            return Response({'data': None, 'message': 'No files uploaded', 'status': False}, status=status.HTTP_400_BAD_REQUEST)

        account_id = int(account_id)
        if drop_duplicates is not None:
            drop_duplicates = drop_duplicates == '1'
        if import_from_last_date is not None:
            import_from_last_date = import_from_last_date == '1'
        upload_parameters = {
            'upload_files': upload_files,
            'account_id': account_id,
        }
        import_service = TransactionImportService()
        uploaded_files = import_service.upload_transaction_files(upload_parameters)
        if not uploaded_files:
            return Response({'data': None, 'message': 'Failed to upload files', 'status': False}, status=status.HTTP_400_BAD_REQUEST)

        failed_uploads = [file for file in uploaded_files if file not in upload_files]
        if failed_uploads:
            logging.info(f"These files uploading failed: {failed_uploads}")
        import_parameters = {
            'account_id': account_id,
            'drop_duplicates': drop_duplicates,
            'import_from_last_date': import_from_last_date,
            'start_date': start_date,
            'end_date': end_date,
            'files': uploaded_files,
        }

        is_imported = import_service.import_transactions(import_parameters)
        if is_imported:
            return Response({'data': {'uploaded_files': uploaded_files}, 'message': 'Imported Successfully', 'status': True}, status=status.HTTP_200_OK)
        return Response({'data': None, 'message': 'Failed to import', 'status': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

