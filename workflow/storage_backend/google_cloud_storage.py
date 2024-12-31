import logging
from io import BytesIO

import pandas as pd
from google.cloud import storage

from workflow.contracts.storage_backend_contract import StorageBackendContract
import pathlib
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential


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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
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

    def read_file(self, file_name, read_config, file_format=None):
        """
        Reads and processes a file from the GCS bucket.

        Args:
            file_name (str): The name of the file in the bucket.
            read_config (dict): Configuration for reading the file.
            file_format (str, optional): The file format. Defaults to inferring from the file extension.

        Returns:
            pd.DataFrame or None: The processed file as a pandas DataFrame, or None if unsupported format.
        """
        try:
            bucket = self._client.bucket(self._bucket_name)
            blob = bucket.blob(file_name)
            data = blob.download_as_string()
            as_byte = BytesIO(data)
            ext = pathlib.Path(file_name).suffix
            if ext == '.csv':
                return self.read_csv_file(as_byte, read_config)
            return None
        except Exception as e:
            logging.exception(f'Error downloading file from bucket {e}')

    def read_all_files(self, prefix, read_config):
        files = self.list_files(prefix)
        file_list = []
        for file in files:
            df = self.read_file(file, read_config)
            file_list.append(df)
        return file_list

    def read_csv_file(self, as_byte, read_config):
        """
        Reads a CSV file into a pandas DataFrame.

        Args:
            as_byte (BytesIO): The CSV file as a byte stream.
            read_config (dict): Configuration for pandas read_csv.

        Returns:
            pd.DataFrame: The CSV file as a DataFrame.
        """
        try:
            return pd.read_csv(as_byte, **read_config)
        except Exception as e:
            logging.exception(f'Error reading file from bucket {e}')
