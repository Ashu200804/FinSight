from minio import Minio
from minio.error import S3Error
import os
import io
from pydantic_settings import BaseSettings, SettingsConfigDict

class MinIOConfig(BaseSettings):
    MINIO_URL: str = os.getenv("MINIO_URL", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "credit-underwriting")
    MINIO_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

minio_config = MinIOConfig()

# Initialize MinIO client
minio_client = Minio(
    minio_config.MINIO_URL,
    access_key=minio_config.MINIO_ACCESS_KEY,
    secret_key=minio_config.MINIO_SECRET_KEY,
    secure=minio_config.MINIO_USE_SSL,
)

def ensure_bucket_exists():
    """Create bucket if it doesn't exist"""
    try:
        if not minio_client.bucket_exists(minio_config.MINIO_BUCKET_NAME):
            minio_client.make_bucket(minio_config.MINIO_BUCKET_NAME)
            print(f"Bucket '{minio_config.MINIO_BUCKET_NAME}' created successfully")
    except Exception as e:
        print(f"Error checking/creating bucket: {e}")

def upload_file(file_data: bytes, file_name: str, entity_id: int, document_type: str) -> str:
    """
    Upload file to MinIO with encryption
    Returns the object path
    """
    try:
        # Create object path: entity_id/document_type/filename
        object_name = f"{entity_id}/{document_type}/{file_name}"
        file_stream = io.BytesIO(file_data)
        
        # Upload file
        minio_client.put_object(
            minio_config.MINIO_BUCKET_NAME,
            object_name,
            file_stream,
            length=len(file_data),
            metadata={"entity_id": str(entity_id), "document_type": document_type}
        )
        
        return object_name
    except S3Error as e:
        raise Exception(f"Error uploading file: {e}")

def download_file(object_name: str) -> bytes:
    """Download file from MinIO"""
    try:
        response = minio_client.get_object(
            minio_config.MINIO_BUCKET_NAME,
            object_name
        )
        return response.read()
    except S3Error as e:
        raise Exception(f"Error downloading file: {e}")

def delete_file(object_name: str) -> bool:
    """Delete file from MinIO"""
    try:
        minio_client.remove_object(
            minio_config.MINIO_BUCKET_NAME,
            object_name
        )
        return True
    except S3Error as e:
        raise Exception(f"Error deleting file: {e}")

def list_files(entity_id: int) -> list:
    """List all files for an entity"""
    try:
        prefix = f"{entity_id}/"
        objects = minio_client.list_objects(
            minio_config.MINIO_BUCKET_NAME,
            prefix=prefix,
            recursive=True
        )
        return [obj.object_name for obj in objects]
    except S3Error as e:
        raise Exception(f"Error listing files: {e}")
