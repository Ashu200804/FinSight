"""
AWS S3 storage backend.

Mirrors the same interface as minio_client.py so callers can swap
STORAGE_BACKEND=s3 without changing any import.

Environment variables required when STORAGE_BACKEND=s3:
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_S3_BUCKET          (bucket name)
  AWS_S3_REGION          (default: ap-south-1)
  AWS_S3_ENDPOINT_URL    (optional: for MinIO-compatible endpoint or localstack)
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET         = os.getenv("AWS_S3_BUCKET", "credit-underwriting")
AWS_S3_REGION         = os.getenv("AWS_S3_REGION", "ap-south-1")
AWS_S3_ENDPOINT_URL   = os.getenv("AWS_S3_ENDPOINT_URL")   # None = use real AWS

_boto_config = Config(
    region_name=AWS_S3_REGION,
    retries={"max_attempts": 3, "mode": "standard"},
    signature_version="s3v4",
)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION,
    endpoint_url=AWS_S3_ENDPOINT_URL,    # None for real S3
    config=_boto_config,
)


# ---------------------------------------------------------------------------
# Bucket bootstrap
# ---------------------------------------------------------------------------

def ensure_bucket_exists() -> None:
    """Create the S3 bucket if it does not exist (idempotent)."""
    try:
        s3_client.head_bucket(Bucket=AWS_S3_BUCKET)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("404", "NoSuchBucket"):
            # Bucket doesn't exist — create it
            if AWS_S3_REGION == "us-east-1":
                s3_client.create_bucket(Bucket=AWS_S3_BUCKET)
            else:
                s3_client.create_bucket(
                    Bucket=AWS_S3_BUCKET,
                    CreateBucketConfiguration={"LocationConstraint": AWS_S3_REGION},
                )

            # Block all public access — documents are private by default
            s3_client.put_public_access_block(
                Bucket=AWS_S3_BUCKET,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls":       True,
                    "IgnorePublicAcls":      True,
                    "BlockPublicPolicy":     True,
                    "RestrictPublicBuckets": True,
                },
            )

            # Enable server-side encryption (AES-256)
            s3_client.put_bucket_encryption(
                Bucket=AWS_S3_BUCKET,
                ServerSideEncryptionConfiguration={
                    "Rules": [{
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }]
                },
            )
            print(f"[S3] Bucket '{AWS_S3_BUCKET}' created with SSE-AES256 and blocked public access.")
        else:
            print(f"[S3] Warning — could not verify bucket: {e}")


# ---------------------------------------------------------------------------
# File operations (same signature as minio_client.py)
# ---------------------------------------------------------------------------

def upload_file(
    file_data: bytes,
    file_name: str,
    entity_id: int,
    document_type: str,
) -> str:
    """
    Upload file to S3.
    Returns the S3 object key (e.g. "42/annual_report/report.pdf").
    """
    object_key = f"{entity_id}/{document_type}/{file_name}"
    try:
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=object_key,
            Body=BytesIO(file_data),
            ContentLength=len(file_data),
            Metadata={
                "entity-id":     str(entity_id),
                "document-type": document_type,
            },
            ServerSideEncryption="AES256",
        )
        return object_key
    except (BotoCoreError, ClientError) as exc:
        raise Exception(f"S3 upload error: {exc}") from exc


def download_file(object_key: str) -> bytes:
    """Download and return raw bytes from S3."""
    try:
        response = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=object_key)
        return response["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        raise Exception(f"S3 download error: {exc}") from exc


def delete_file(object_key: str) -> bool:
    """Delete an object from S3."""
    try:
        s3_client.delete_object(Bucket=AWS_S3_BUCKET, Key=object_key)
        return True
    except (BotoCoreError, ClientError) as exc:
        raise Exception(f"S3 delete error: {exc}") from exc


def list_files(entity_id: int) -> list[str]:
    """List all object keys for a given entity (prefix search)."""
    prefix = f"{entity_id}/"
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=AWS_S3_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys
    except (BotoCoreError, ClientError) as exc:
        raise Exception(f"S3 list error: {exc}") from exc


def generate_presigned_url(
    object_key: str,
    expiry_seconds: int = 3600,
    http_method: str = "GET",
) -> str:
    """
    Generate a time-limited pre-signed URL for secure, direct browser access
    to a document without streaming through the API server.
    """
    operation = "get_object" if http_method.upper() == "GET" else "put_object"
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=operation,
            Params={"Bucket": AWS_S3_BUCKET, "Key": object_key},
            ExpiresIn=expiry_seconds,
        )
        return url
    except (BotoCoreError, ClientError) as exc:
        raise Exception(f"S3 presigned URL error: {exc}") from exc
