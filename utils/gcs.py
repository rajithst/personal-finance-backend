import logging
import os
import json
import time
from io import BytesIO
from google.cloud import storage


        
class GCSHandler:
    def __init__(self):
        self.gcs_credentials = os.getenv("GCS_API_KEY", None)
        print('gcs credentials: ', self.gcs_credentials)
        print(type(self.gcs_credentials))
        if not self.gcs_credentials:
            raise EnvironmentError(f"GCS_API_KEY not set")
        json_credentials = json.loads(self.gcs_credentials)
        print('json credentials: ', self.gcs_credentials)
        self.client = storage.Client.from_service_account_info(info=json_credentials)

    def upload_file(self, bucket_name, source_file_name, destination_blob_name):
        """Uploads a file to the specified bucket."""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        print(f"File {source_file_name} uploaded to {destination_blob_name}.")

    def download_file(self, bucket_name, source_blob_name, destination_file_name):
        """Downloads a file from the specified bucket."""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        print(f"File {source_blob_name} downloaded to {destination_file_name}.")

    def list_files(self, bucket_name, prefix=None):
        """Lists files in the specified bucket."""

        blobs = self.client.list_blobs(bucket_name, prefix=prefix)
        file_list = []
        for blob in blobs:
            if blob.name != prefix.rstrip('/') and not blob.name.endswith('/'):
                file_list.append(blob.name)
        logging.info('loading data from bucket {}: {}'.format(bucket_name, file_list))
        return file_list

    def delete_file(self, bucket_name, file_name):
        """Deletes a file from the specified bucket."""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.delete()
        print(f"File {file_name} deleted.")

    def get_blob(self, bucket_name, file_name):
        logging.info(f"Downloading file from bucket {file_name}")
        try:
            time.sleep(10)
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(file_name)
            data = blob.download_as_string()
            return BytesIO(data)
        except Exception as e:
            logging.error(e)

