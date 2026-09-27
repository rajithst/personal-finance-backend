from google.cloud import storage
import datetime
from django.core.exceptions import PermissionDenied
from django.conf import settings

def upload_payslip_document(file_obj, user_id, company_slug, year, month, metadata_dict):
    """Uploads a payslip PDF to GCS and returns the URI."""
    bucket_name = getattr(settings, 'GCP_STORAGE_BUCKET', 'personal-finance-dev')
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    filename = f"{year}-{month:02d}_{company_slug}_payslip.pdf"
    blob_path = f"career_vault/users/user_{user_id}/companies/{company_slug}/payslips/{year}/{filename}"
    
    blob = bucket.blob(blob_path)
    blob.metadata = metadata_dict
    
    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type='application/pdf')
    
    return f"gs://{bucket_name}/{blob_path}"

def generate_signed_url(gcs_uri, user_id, requesting_user):
    """Generates a signed URL to view the document."""
    if str(user_id) != str(requesting_user.id):
        raise PermissionDenied("You do not have permission to access this document.")
        
    if not gcs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS URI")
        
    path_parts = gcs_uri.replace("gs://", "").split("/", 1)
    bucket_name = path_parts[0]
    blob_name = path_parts[1]
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="GET"
    )
    return url
