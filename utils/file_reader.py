import os

import pandas as pd
from django.conf import settings
from utils.gcs import GCSHandler


class BaseReader:
    def __init__(self):
        self.bucket_name = settings.BUCKET_NAME
        self.is_dev_env = settings.ENV == 'dev'
        self.blob_handler = None
        if not self.is_dev_env:
            self.blob_handler = GCSHandler()

    def get_files(self, target_path: str):
        if self.is_dev_env:
            data_path = os.path.join(settings.MEDIA_ROOT, target_path)
            files = os.listdir(data_path)
        else:
            files = self.blob_handler.list_files(bucket_name=self.bucket_name, prefix=target_path)
        return files

    def read_single_file(self, file_name, read_config):
        if self.is_dev_env:
            blob_data = os.path.join(settings.MEDIA_ROOT, file_name)
        else:
            blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file_name)
        df = pd.read_csv(blob_data, **read_config)
        return df

    def read_all_files(self, target_path, read_config):
        files = self.get_files(target_path=target_path)
        results = []
        for file in files:
            if self.is_dev_env:
                blob_data = file
            else:
                blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data, **read_config)
            results.append(df)
        if results:
            return pd.concat(results)
        else:
            return None



