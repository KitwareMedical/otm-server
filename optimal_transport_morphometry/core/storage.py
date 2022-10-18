import pathlib
from typing import TYPE_CHECKING, Optional

import boto3
import botocore
from django.conf import settings
from django.core.files.storage import get_storage_class
from s3_file_field import S3FileField

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

# Import storages
try:
    from storages.backends.s3boto3 import S3Boto3Storage
except ImportError:
    # This should only be used for type interrogation, never instantiation
    S3Boto3Storage = type('FakeS3Boto3Storage', (), {})
try:
    from minio_storage.storage import MinioStorage
except ImportError:
    # This should only be used for type interrogation, never instantiation
    MinioStorage = type('FakeMinioStorage', (), {})


def get_boto_client(config: Optional[botocore.client.Config] = None) -> 'S3Client':
    """Return an s3 client from the current storage."""
    storage = get_storage_class()
    if issubclass(storage, MinioStorage):
        return boto3.client(
            's3',
            endpoint_url=f'http://{settings.MINIO_STORAGE_ENDPOINT}',
            aws_access_key_id=settings.MINIO_STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_STORAGE_SECRET_KEY,
            region_name='us-east-1',
            config=config,
        )

    if issubclass(storage, S3Boto3Storage):
        return storage.connection.meta.client

    raise Exception('Unsupported Storage')


def get_bucket_name():
    storage = get_storage_class()
    if issubclass(storage, MinioStorage):
        return settings.MINIO_STORAGE_MEDIA_BUCKET_NAME
    if issubclass(storage, S3Boto3Storage):
        return settings.AWS_STORAGE_BUCKET_NAME

    raise Exception('Unsupported Storage')


def upload_local_file(filepath: str):
    client = get_boto_client(
        config=botocore.client.Config(
            signature_version=botocore.UNSIGNED,
        )
    )

    # Upload file
    path = pathlib.Path(filepath)
    bucket_name = get_bucket_name()
    object_key = S3FileField.uuid_prefix_filename('', path.name)
    client.upload_file(Filename=str(path), Bucket=bucket_name, Key=object_key)

    # Returned URL is unsigned due to config used above
    url = client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
    )
    return url
