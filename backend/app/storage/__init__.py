"""
Storage backend router.

Set the STORAGE_BACKEND environment variable to choose the backend:
  STORAGE_BACKEND=minio    (default — local dev with MinIO)
  STORAGE_BACKEND=s3       (production — AWS S3)

All callers should import from here:
  from app.storage import upload_file, download_file, delete_file, list_files, ensure_bucket_exists
"""

import os

_backend = os.getenv("STORAGE_BACKEND", "minio").lower()

if _backend == "s3":
    from app.storage.s3_client import (        # noqa: F401
        ensure_bucket_exists,
        upload_file,
        download_file,
        delete_file,
        list_files,
        generate_presigned_url,
    )
else:
    from app.storage.minio_client import (     # noqa: F401
        ensure_bucket_exists,
        upload_file,
        download_file,
        delete_file,
        list_files,
    )

    def generate_presigned_url(object_key: str, expiry_seconds: int = 3600, http_method: str = "GET") -> str:
        """MinIO pre-signed URLs (local dev only)."""
        from app.storage.minio_client import minio_client, minio_config
        return minio_client.presigned_get_object(
            minio_config.MINIO_BUCKET_NAME,
            object_key,
            expires=__import__("datetime").timedelta(seconds=expiry_seconds),
        )
