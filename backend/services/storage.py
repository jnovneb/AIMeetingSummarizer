# services/storage.py
# Simple MinIO (S3-compatible) wrapper used by the app to store audio and PDFs.
# Configure using environment variables described in README.

from minio import Minio
from minio.error import S3Error
import os

# Read config from environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() in ("1", "true", "yes")

# Buckets
AUDIO_BUCKET = os.getenv("MINIO_AUDIO_BUCKET", "meeting-audios")
PDF_BUCKET = os.getenv("MINIO_PDF_BUCKET", "meeting-pdfs")

# Initialize client
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)


def ensure_bucket(bucket_name: str):
    """Create bucket if it doesn't exist."""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
    except S3Error as e:
        raise RuntimeError(f"MinIO error ensuring bucket {bucket_name}: {e}")


def upload_file(local_path: str, bucket_name: str, object_name: str = None) -> str:
    """
    Upload a file to MinIO and return the object name.
    :param local_path: local file path
    :param bucket_name: target bucket
    :param object_name: name to store in bucket (defaults to basename)
    :return: object_name stored
    """
    import os
    ensure_bucket(bucket_name)
    if object_name is None:
        object_name = os.path.basename(local_path)
    client.fput_object(bucket_name, object_name, local_path)
    return object_name


def get_presigned_url(bucket_name: str, object_name: str, expires: int = 24*3600) -> str:
    """
    Generate a presigned URL for downloading an object.
    :param expires: seconds until expiration
    """
    try:
        url = client.get_presigned_url("GET", bucket_name, object_name, expires=expires)
        return url
    except S3Error as e:
        raise RuntimeError(f"MinIO error generating presigned URL: {e}")
