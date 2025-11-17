"""Storage service for S3 operations."""

from functools import lru_cache
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def _get_s3_client():
    """Get cached S3 client instance.

    Returns:
        boto3 S3 client configured with settings
    """
    # Build client kwargs - only include credentials if explicitly provided
    # This allows boto3 to fall back to default credential chain (~/.aws/credentials, env vars, IAM roles)
    client_kwargs = {
        "service_name": "s3",
        "region_name": settings.aws_region,
    }
    
    # Only add credentials if they're explicitly set (not None)
    # If None, boto3 will use default credential chain
    if settings.aws_access_key_id is not None:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
    if settings.aws_secret_access_key is not None:
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    
    return boto3.client(**client_kwargs)


def upload_bytes_to_s3(
    bucket: str,
    key: str,
    data: bytes,
    content_type: Optional[str] = None,
) -> None:
    """Upload bytes to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)
        data: Bytes to upload
        content_type: Optional content type (MIME type)

    Raises:
        RuntimeError: If upload fails
    """
    client = _get_s3_client()
    extra_args: dict[str, str] = {}
    if content_type:
        extra_args["ContentType"] = content_type

    try:
        client.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to upload object {key} to bucket {bucket}") from exc


def download_bytes_from_s3(bucket: str, key: str) -> bytes:
    """Download bytes from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)

    Returns:
        Downloaded bytes

    Raises:
        RuntimeError: If download fails
    """
    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=bucket, Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to download object {key} from bucket {bucket}") from exc

    body = response.get("Body")
    if body is None:
        raise RuntimeError(f"No content returned for object {key} from bucket {bucket}")

    return body.read()


def generate_presigned_get_url(
    bucket: str,
    key: str,
    expires_in: int = 3600,
) -> str:
    """Generate a presigned URL for getting an object from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)
        expires_in: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL string

    Raises:
        RuntimeError: If URL generation fails
    """
    client = _get_s3_client()
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Failed to generate presigned URL for object {key} in bucket {bucket}"
        ) from exc


def generate_presigned_put_url(
    bucket: str,
    key: str,
    expires_in: int = 3600,
) -> str:
    """Generate a presigned URL for putting an object to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)
        expires_in: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL string

    Raises:
        RuntimeError: If URL generation fails
    """
    client = _get_s3_client()
    try:
        return client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Failed to generate presigned PUT URL for object {key} in bucket {bucket}"
        ) from exc


def delete_from_s3(bucket: str, key: str) -> None:
    """Delete an object from S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)

    Raises:
        RuntimeError: If deletion fails
    """
    client = _get_s3_client()
    try:
        client.delete_object(Bucket=bucket, Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to delete object {key} from bucket {bucket}") from exc

