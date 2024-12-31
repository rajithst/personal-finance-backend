from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.services.transaction_import_service import TransactionImportService


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
            return Response({'message': 'Account must be selected', 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        if not upload_files:
            return Response({'message': 'No files uploaded', 'status': False}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({'message': 'Failed to upload files', 'status': False}, status=status.HTTP_400_BAD_REQUEST)

        failed_uploads = [file for file in uploaded_files if file not in upload_files]
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
            return Response({'message': 'Imported Successfully', 'status': True}, status=status.HTTP_200_OK)
        return Response({'message': 'Failed to import', 'status': False}, status=status.HTTP_400_BAD_REQUEST)
