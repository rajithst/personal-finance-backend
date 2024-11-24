import logging
import os
import time

from django.conf import settings

from oauth.middleware import get_current_user
from django.core.files.storage import default_storage

from utils.gcs import GCSHandler


class FileUploadService:
    def __init__(self):
        self.is_dev_env = settings.ENV == 'dev'

    def _upload_file(self, file, file_name):
        try:
            if self.is_dev_env:
                file_path = os.path.join(settings.MEDIA_ROOT, file_name)
                if not os.path.exists(os.path.dirname(file_path)):
                    os.makedirs(os.path.dirname(file_path))
                with default_storage.open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
            else:
                gcs_handler = GCSHandler()
                gcs_handler.upload_file(settings.BUCKET_NAME, file, file_name)
            return True
        except Exception as e:
            logging.exception('error uploading file %s', file.name)
            return False
    def upload_transaction_files(self, upload_params):
        file_names = self._handle_file_upload(upload_params, target='finance')
        return file_names

    def upload_trade_files(self, upload_params):
        file_names = self._handle_file_upload(upload_params, target='investments')
        return file_names

    def _handle_file_upload(self, upload_params, target):
        user = get_current_user()
        upload_files = upload_params['upload_files']
        account_id = upload_params['account_id']
        file_names = []
        for upload_file in upload_files:
            upload_file_name = f"{int(time.time())}_{upload_file.name}"
            file_name = f"user_{user.id}/{target}/acc_{account_id}/{upload_file_name}"
            is_uploaded = self._upload_file(upload_file, file_name)
            if is_uploaded:
                file_names.append(file_name)
        return file_names