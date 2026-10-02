import os
import re
import datetime
import mimetypes
from django.core.exceptions import PermissionDenied
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils.text import slugify
from django.conf import settings
from google.cloud import storage

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

    bucket_name = getattr(settings, 'GCP_STORAGE_BUCKET', None) or getattr(settings, 'BUCKET_NAME', None) or 'personal-finance-dev'
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    blob = bucket.blob(blob_path)
    blob.metadata = metadata_dict
    
    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type='application/pdf')
    
    return f"gs://{bucket_name}/{blob_path}"


def upload_career_document(file_obj, user_id, company_slug='general', doc_type='other', original_filename=None, metadata_dict=None):
    """
    Uploads a career document (contract, offer letter, tax slip, etc.)
    to GCS (prod) or Local Media (dev) and returns the URI (gs://... or local://...).
    """
    company_slug_clean = slugify(str(company_slug)) if company_slug else 'general'
    doc_type_clean = slugify(str(doc_type)) if doc_type else 'other'
    safe_name = os.path.basename(original_filename or 'document.pdf')
    safe_name = re.sub(r'[^\w\.-]', '_', safe_name)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{safe_name}"
    blob_path = f"career_vault/users/user_{user_id}/companies/{company_slug_clean}/documents/{doc_type_clean}/{filename}"

    if getattr(settings, 'DEBUG', False):
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        local_path = os.path.join(media_root, blob_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        file_obj.seek(0)
        with open(local_path, 'wb') as f:
            f.write(file_obj.read())
        return f"local://{blob_path}"

    bucket_name = getattr(settings, 'GCP_STORAGE_BUCKET', None) or getattr(settings, 'BUCKET_NAME', None) or 'personal-finance-dev'
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    blob = bucket.blob(blob_path)
    if metadata_dict:
        blob.metadata = metadata_dict

    content_type = getattr(file_obj, 'content_type', None) or mimetypes.guess_type(safe_name)[0] or 'application/pdf'
    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type=content_type)

    return f"gs://{bucket_name}/{blob_path}"


def generate_download_signature(doc_id, user_id):
    """Generates a secure timestamped signature for downloading a career document."""
    signer = TimestampSigner(salt='career-document-download')
    return signer.sign(f"{doc_id}:{user_id}")


def verify_download_signature(signature, doc_id, user_id, max_age=86400):
    """Verifies a timestamped signature for downloading a career document (default 24 hours)."""
    signer = TimestampSigner(salt='career-document-download')
    try:
        val = signer.unsign(signature, max_age=max_age)
        sig_doc_id, sig_user_id = val.split(':', 1)
        return str(sig_doc_id) == str(doc_id) and str(sig_user_id) == str(user_id)
    except (BadSignature, SignatureExpired, ValueError):
        return False


def generate_document_download_url(doc):
    """Returns the backend download URL with signature for direct viewing/downloading."""
    if not doc or not doc.pk:
        return None
    sig = generate_download_signature(doc.pk, doc.user_id)
    return f"/finance/career/documents/{doc.pk}/download/?sig={sig}"


def open_document_stream(doc):
    """
    Opens and returns (stream, content_type, filename, size) for a CareerDocument.
    Supports gs://, local://, and legacy local media paths.
    Returns None if file is not found.
    """
    if not doc or not doc.file:
        return None

    raw_path = str(doc.file.name if hasattr(doc.file, 'name') else doc.file)
    if not raw_path:
        return None

    filename = doc.file_name_original or os.path.basename(raw_path.split('?')[0]) or 'document.pdf'
    content_type = doc.mime_type or mimetypes.guess_type(filename)[0] or 'application/pdf'
    size = doc.file_size

    if raw_path.startswith('gs://'):
        try:
            path_parts = raw_path.replace('gs://', '').split('/', 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if not blob.exists():
                return None
            stream = blob.open('rb')
            size = blob.size or size
            if blob.content_type:
                content_type = blob.content_type
            return (stream, content_type, filename, size)
        except Exception:
            return None

    if raw_path.startswith('local://') or raw_path.startswith('local:/'):
        clean_path = raw_path.split('local:', 1)[-1].lstrip('/')
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        full_path = os.path.join(media_root, clean_path)
        if not os.path.exists(full_path):
            return None
        stream = open(full_path, 'rb')
        size = os.path.getsize(full_path)
        return (stream, content_type, filename, size)

    # Legacy relative path (e.g. career_docs/2026/10/...)
    media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
    full_path = os.path.join(media_root, raw_path.lstrip('/'))
    if os.path.exists(full_path):
        stream = open(full_path, 'rb')
        size = os.path.getsize(full_path)
        return (stream, content_type, filename, size)

    return None


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
