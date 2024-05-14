import logging
import os
from io import BytesIO
from azure.storage.blob import BlobServiceClient


class AzureBlobHandler:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(os.environ['STORAGE_CONNECTION_STRING'])

    def list_files(self, bucket_name, prefix=None):
        """Lists files in the specified bucket."""
        container_client = self.client.get_container_client(bucket_name)
        blob_list = container_client.list_blobs(name_starts_with=prefix)
        file_list = []
        for blob in blob_list:
            file_list.append(blob.name)
        return file_list

    def get_blob(self, bucket_name, file_name):
        container_client = self.client.get_container_client(bucket_name)
        blob_client = container_client.get_blob_client(file_name)
        blob_data = blob_client.download_blob().readall()
        return BytesIO(blob_data)
