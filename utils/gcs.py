import logging
from io import BytesIO

        
class GCSHandler:
    def __init__(self, project_id):
        self.client = None

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
        bucket = self.client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
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
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        data = blob.download_as_string()
        return BytesIO(data)
