import logging
import os

import pandas as pd
from django.core.files.storage import default_storage

from django.conf import settings

from workflow.contracts.storage_backend_contract import StorageBackendContract


class LocalStorageHandler(StorageBackendContract):

    def upload_file(self, file, file_name, content_type=None):
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        try:
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with default_storage.open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            return True
        except Exception as e:
            logging.exception('failed to write files to the storage backend')
            return False

    def list_files(self, prefix=None):
        data_path = os.path.join(settings.MEDIA_ROOT, prefix)
        return os.listdir(data_path.__str__())

    def delete_file(self, file_name):
        pass

    def read_file(self, file_name, read_config, file_type=None):
        file = os.path.join(settings.MEDIA_ROOT, file_name)
        return pd.read_csv(file.__str__(), **read_config)

    def read_all_files(self, prefix, read_config, file_type=None):
        files = self.list_files(prefix)
        all_files = []
        for file in files:
            df = pd.read_csv(file.__str__(), **read_config)
            all_files.append(df)
        return all_files
