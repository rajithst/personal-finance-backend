import logging
import os
import time

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.connector.card_loader import CardLoader
from transactions.models import Transaction, Account
from utils.gcs import GCSHandler


class TransactionImportView(APIView):
    parser_classes = (MultiPartParser,)
    def post(self, request):
        upload_files = request.FILES.getlist('files')
        account_id = request.data.get('account_id')
        drop_duplicates = request.data.get('drop_duplicates')
        import_from_last_date = request.data.get('import_from_last_date')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        if not account_id or not upload_files:
            return Response({'error': 'Missing file'}, status=status.HTTP_400_BAD_REQUEST)
        is_dev_env = settings.ENV == 'dev'
        bucket_name = settings.BUCKET_NAME
        user = self.request.user
        file_names = []
        try:
            for upload_file in upload_files:
                upload_file_name = f"{int(time.time())}_{upload_file.name}"
                file_name = f"user_{user.id}/finance/acc_{account_id}/{upload_file_name}"
                if is_dev_env:
                    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
                    if not os.path.exists(os.path.dirname(file_path)):
                        os.makedirs(os.path.dirname(file_path))
                    with default_storage.open(file_path, 'wb+') as destination:
                        for chunk in upload_file.chunks():
                            destination.write(chunk)
                else:
                    gcs_handler = GCSHandler()
                    gcs_handler.upload_file(bucket_name, upload_file, file_name)
                file_names.append(file_name)
            self.process_data(account_id, drop_duplicates, import_from_last_date, start_date, end_date, file_names)
            return Response({'message': 'File uploaded successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logging.error(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        account_id = self.request.get('account_id', None)
        file_name = self.request.get('file_name', None)
        if not account_id:
            return Response({'error': 'Missing account_id'}, status=status.HTTP_400_BAD_REQUEST)
        return self.process_data(account_id, [file_name])

    def process_data(self, account_id, drop_duplicates, import_from_last_date, start_date=None, end_date=None, file_names=None, ):
        user = self.request.user
        account_id = int(account_id)
        account_data = Account.objects.filter(user_id=user.id, id=account_id).first()
        loader = CardLoader(request_user=user,
                            drop_duplicates=drop_duplicates,
                            import_from_last_date=import_from_last_date,
                            start_date=start_date,
                            end_date=end_date,
                            account=account_data,
                            file_names=file_names)
        expenses = loader.process()
        if expenses is not None and not expenses.empty:
            last_import_date = expenses['date'].max()
            expense_records = expenses.to_dict('records')
            try:
                expense_objects = []
                for expense in expense_records:
                    expense_objects.append(Transaction(**expense))
                Transaction.objects.bulk_create(expense_objects)
                Account.objects.filter(user_id=user.id, id=account_id).update(last_import_date=last_import_date)
                return Response({'message': 'Success'}, status=status.HTTP_200_OK)
            except Exception as e:
                logging.exception('Error importing Expenses objects')
                return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)