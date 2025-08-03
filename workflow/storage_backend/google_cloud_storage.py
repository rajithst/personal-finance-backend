import io
import logging

import pandas as pd
from django.conf import settings
from google.cloud import storage

from workflow.contracts.storage_backend_contract import StorageBackendContract


class GCSHandler(StorageBackendContract):
    """
    A handler for interacting with Google Cloud Storage (GCS).

    Provides methods for uploading, downloading, reading, and listing files in a GCS bucket.
    """

    def __init__(self, bucket_name=None):
        """
        Initializes the GCSHandler with a specified bucket name.

        Args:
            bucket_name (str, optional): The name of the GCS bucket. Defaults to the bucket defined in settings.
        """
        self._client = storage.Client()
        self._bucket_name = bucket_name or settings.BUCKET_NAME

    def upload_file(self, file, file_name, content_type=None):
        """
        Uploads a file to the GCS bucket with retry logic.

        Args:
            file (file-like object): The file to upload.
            file_name (str): The name of the file in the GCS bucket.
            content_type (str, optional): The content type of the file. Defaults to None.

        Raises:
            Exception: If the upload fails after retries.
        """
        try:
            bucket = self._client.bucket(self._bucket_name)
            blob = bucket.blob(file_name)
            blob.upload_from_file(file)
            return True
        except Exception as e:
            logging.exception(f'Failed to upload file {e}')

    def list_files(self, prefix=None):
        """
        Lists files in the GCS bucket with optional filtering and pagination.

        Args:
            prefix (str, optional): The prefix to filter files. Defaults to None.
            max_results (int, optional): The maximum number of files to list. Defaults to None.

        Returns:
            list[str]: A list of file names in the bucket.
        """
        blobs = self._client.list_blobs(self._bucket_name, prefix=prefix)
        file_list = []
        for blob in blobs:
            if blob.name != prefix.rstrip('/') and not blob.name.endswith('/'):
                file_list.append(blob.name)
        return file_list

    def delete_file(self, file_name):
        """Deletes a file from the specified bucket."""
        bucket = self._client.bucket(self._bucket_name)
        blob = bucket.blob(file_name)
        blob.delete()

    def read_file(self, file_name, read_config=None):
        """
        Reads a file from the GCS bucket.
        Args:
            file_name (str): The name of the file in the bucket.
            read_config (dict, optional): The read configuration for the file. Defaults to None.
        Returns:
            io.StringIO: The file as a TextIOWrapper object.
        """
        try:
            bucket = self._client.bucket(self._bucket_name)
            blob = bucket.blob(file_name)
            encoding = read_config.get('encoding') if read_config else 'utf-8'
            file_content = blob.download_as_text(encoding=encoding)
            return io.StringIO(file_content)
        except Exception as e:
            logging.exception(f'Error downloading file from bucket {e}')

    def read_all_files(self, prefix, read_config=None):
        """
        Reads all files in the GCS bucket with the specified prefix.

        Args:
            prefix (str): The prefix to filter files.
            read_config (dict, optional): The read configuration for the files. Defaults to None.
        Returns:
            list[pd.DataFrame]: A list of files as TextIOWrapper objects.
        """
        files = self.list_files(prefix)
        file_list = []
        for file in files:
            df = self.read_file(file, read_config)
            file_list.append(df)
        return file_list

    def read_csv(self, file_name, read_config=None):
        """
        Reads a CSV file from the GCS bucket.

        Args:
            file_name (str): The name of the file in the bucket.
            read_config (dict, optional): The read configuration for the file. Defaults to None.

        Returns:
            pd.DataFrame or None: The CSV file as a pandas DataFrame, or None if unsupported format.
        """
        try:
            bucket = self._client.bucket(self._bucket_name)
            blob = bucket.blob(file_name)
            data = blob.download_as_string()
            as_byte = io.BytesIO(data)
            return pd.read_csv(as_byte, **read_config)
        except Exception as e:
            logging.exception(f'Error reading CSV file from bucket {e}')
            return None
