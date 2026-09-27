import os
from google.cloud import storage
import datetime
from django.core.exceptions import PermissionDenied
from django.conf import settings

def upload_payslip_document(file_obj, user_id, company_slug, year, month, metadata_dict):
    """Uploads a payslip PDF to GCS or Local Storage and returns the URI."""
    filename = f"{year}-{month:02d}_{company_slug}_payslip.pdf"
    blob_path = f"career_vault/users/user_{user_id}/companies/{company_slug}/payslips/{year}/{filename}"

    if getattr(settings, 'DEBUG', False):
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        local_path = os.path.join(media_root, blob_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        file_obj.seek(0)
        with open(local_path, 'wb') as f:
            f.write(file_obj.read())
        return f"local://{blob_path}"

    bucket_name = getattr(settings, 'GCP_STORAGE_BUCKET', 'personal-finance-dev')
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    blob = bucket.blob(blob_path)
    blob.metadata = metadata_dict
    
    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type='application/pdf')
    
    return f"gs://{bucket_name}/{blob_path}"

def generate_signed_url(gcs_uri, user_id, requesting_user):
    """Generates a signed URL to view the document."""
    if str(user_id) != str(requesting_user.id):
        raise PermissionDenied("You do not have permission to access this document.")
        
    if gcs_uri.startswith("local://"):
        blob_path = gcs_uri.replace("local://", "")
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        return f"{media_url}{blob_path}"
        
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
