import logging
from io import BytesIO
from google.cloud import storage


        
class GCSHandler:
    def __init__(self):
        self.client = storage.Client()

    def upload_file(self, bucket_name, source_file_name, destination_blob_name):
        """Uploads a file to the specified bucket."""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logging.info(f"File {source_file_name} uploaded to {destination_blob_name}.")

    def move_blob(self, bucket_name, source_file_name, destination_file_name):
        """Move a blob from one directory to another within the same bucket."""
        bucket = self.client.bucket(bucket_name)
        source_blob = bucket.blob(source_file_name)
        destination_blob = bucket.blob(destination_file_name)
        source_blob.copy_to(destination_blob)
        source_blob.delete()
        logging.info(f'File {source_file_name} moved to {destination_file_name}.')

    def download_file(self, bucket_name, source_blob_name, destination_file_name):
        """Downloads a file from the specified bucket."""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        logging.info(f"File {source_blob_name} downloaded to {destination_file_name}.")

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
        logging.info(f"File {file_name} deleted.")

    def get_blob(self, bucket_name, file_name, move_to_completed=True):
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(file_name)
            data = blob.download_as_string()
            if move_to_completed:
                destination_file = 'processed/' + file_name
                self.move_blob(bucket_name, file_name, destination_file)
            logging.info(f"Downloaded file from bucket {file_name}")
            return BytesIO(data)
        except Exception as e:
            logging.exception('Error downloading file from bucket')

