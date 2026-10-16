import os
import re
import datetime
import mimetypes
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils.text import slugify
from django.conf import settings
from google.cloud import storage

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/webp',
}

signer = TimestampSigner(salt='personal_vault_secure_salt')


def validate_vault_file(file_obj):
    """Validates file size, file extension, and MIME type."""
    # Size check
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)

    if size > MAX_FILE_SIZE:
        raise ValidationError(f"File size ({size / (1024 * 1024):.1f} MB) exceeds maximum allowed 25 MB.")

    raw_name = getattr(file_obj, 'name', 'document.pdf') or 'document.pdf'
    base_name = os.path.basename(raw_name)
    _, ext = os.path.splitext(base_name)
    ext_lower = ext.lower()

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File extension '{ext_lower}' is not allowed. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    mime_type, _ = mimetypes.guess_type(base_name)
    if not mime_type or mime_type not in ALLOWED_MIME_TYPES:
        if ext_lower in ('.jpg', '.jpeg'):
            mime_type = 'image/jpeg'
        elif ext_lower == '.png':
            mime_type = 'image/png'
        elif ext_lower == '.webp':
            mime_type = 'image/webp'
        elif ext_lower == '.pdf':
            mime_type = 'application/pdf'
        else:
            raise ValidationError(f"MIME type '{mime_type}' is not allowed.")

    clean_name = re.sub(r'[^\w\.-]', '_', base_name)
    return {
        'safe_name': clean_name,
        'size': size,
        'mime_type': mime_type,
    }


def upload_personal_document(file_obj, user_id, category='general', doc_type='other', original_filename=None):
    """
    Validates and uploads a personal vault document to local media (dev) or GCS (prod).
    Returns file_uri string: 'local://...' or 'gs://...'.
    """
    validation_info = validate_vault_file(file_obj)
    safe_name = validation_info['safe_name']

    cat_slug = slugify(str(category)) if category else 'general'
    doc_type_slug = slugify(str(doc_type)) if doc_type else 'other'
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{safe_name}"

    blob_path = f"personal_vault/users/user_{user_id}/{cat_slug}/{doc_type_slug}/{filename}"

    if getattr(settings, 'DEBUG', False):
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        local_path = os.path.join(media_root, blob_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        file_obj.seek(0)
        with open(local_path, 'wb') as f:
            f.write(file_obj.read())
        return f"local://{blob_path}"

    bucket_name = getattr(settings, 'GCP_STORAGE_BUCKET', None) or getattr(settings, 'BUCKET_NAME', None) or 'personal-finance-dev'
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        file_obj.seek(0)
        blob.upload_from_file(file_obj, content_type=validation_info['mime_type'])
        return f"gs://{bucket_name}/{blob_path}"
    except Exception:
        # Fallback to local storage in non-cloud test/dev run
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        local_path = os.path.join(media_root, blob_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        file_obj.seek(0)
        with open(local_path, 'wb') as f:
            f.write(file_obj.read())
        return f"local://{blob_path}"


def generate_vault_signature(doc_id, user_id):
    """Generates a signed token valid for 15 minutes."""
    data = f"{doc_id}:{user_id}"
    return signer.sign(data)


def verify_vault_signature(token, max_age=900):
    """Verifies token signature and expiration (default 15 minutes = 900s)."""
    try:
        unsigned = signer.unsign(token, max_age=max_age)
        doc_id_str, user_id_str = unsigned.split(':', 1)
        return int(doc_id_str), int(user_id_str)
    except (BadSignature, SignatureExpired, ValueError):
        raise PermissionDenied("Invalid or expired download signature.")
