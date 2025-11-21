from __future__ import annotations

from functools import lru_cache
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings


def _get_bucket_region() -> str:
    """Get the actual region of the S3 bucket.
    
    If S3_REGION is set, use it. Otherwise, detect the bucket's region.
    """
    settings = get_settings()
    
    # If region is explicitly set, use it
    if settings.s3_region:
        return settings.s3_region
    
    # Otherwise, detect the bucket's region
    try:
        # Create a client without region to query bucket location
        temp_kwargs = {}
        if settings.s3_endpoint_url:
            temp_kwargs["endpoint_url"] = settings.s3_endpoint_url
        if settings.s3_access_key_id:
            temp_kwargs["aws_access_key_id"] = settings.s3_access_key_id
        if settings.s3_secret_access_key:
            temp_kwargs["aws_secret_access_key"] = settings.s3_secret_access_key
        temp_client = boto3.client("s3", **temp_kwargs)
        response = temp_client.get_bucket_location(Bucket=settings.s3_bucket_name)
        # get_bucket_location returns None for us-east-1 (legacy behavior)
        region = response.get("LocationConstraint") or "us-east-1"
        return region
    except Exception:
        # Fallback to us-east-1 if detection fails
        return "us-east-1"


@lru_cache
def _get_s3_client():
    settings = get_settings()
    # Explicitly use Signature Version 4 (AWS4-HMAC-SHA256) for presigned URLs
    config = Config(signature_version='s3v4')
    # Get the correct region (auto-detect if not set)
    region = _get_bucket_region()
    
    # Build client kwargs - only include credentials if explicitly set
    # Otherwise boto3 will use default credential chain (AWS_ACCESS_KEY_ID env vars, IAM roles, etc.)
    client_kwargs = {
        "region_name": region,
        "config": config,
    }
    
    if settings.s3_endpoint_url:
        client_kwargs["endpoint_url"] = settings.s3_endpoint_url
    
    # Only pass credentials if explicitly set (allows fallback to AWS_ACCESS_KEY_ID env vars)
    if settings.s3_access_key_id:
        client_kwargs["aws_access_key_id"] = settings.s3_access_key_id
    if settings.s3_secret_access_key:
        client_kwargs["aws_secret_access_key"] = settings.s3_secret_access_key
    
    return boto3.client("s3", **client_kwargs)


def upload_bytes_to_s3(
    *,
    bucket_name: str,
    key: str,
    data: bytes,
    content_type: Optional[str] = None,
) -> None:
    client = _get_s3_client()
    extra_args: dict[str, str] = {}
    if content_type:
        extra_args["ContentType"] = content_type

    try:
        client.put_object(Bucket=bucket_name, Key=key, Body=data, **extra_args)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to upload object {key} to bucket {bucket_name}") from exc


def generate_presigned_get_url(
    *,
    bucket_name: str,
    key: str,
    expires_in: int = 3600,
) -> str:
    client = _get_s3_client()
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(
            f"Failed to generate presigned URL for object {key} in bucket {bucket_name}"
        ) from exc


def check_s3_object_exists(*, bucket_name: str, key: str) -> bool:
    """Check if an S3 object exists without downloading it."""
    client = _get_s3_client()
    try:
        client.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code == "404" or error_code == "NoSuchKey":
            return False
        # Re-raise for other errors (permissions, etc.)
        raise RuntimeError(f"Failed to check if object {key} exists in bucket {bucket_name}") from exc
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to check if object {key} exists in bucket {bucket_name}") from exc


def delete_s3_object(*, bucket_name: str, key: str) -> None:
    """Delete an S3 object. Silently succeeds if object doesn't exist."""
    client = _get_s3_client()
    try:
        client.delete_object(Bucket=bucket_name, Key=key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        # Ignore 404/NoSuchKey errors (object already doesn't exist)
        if error_code not in ("404", "NoSuchKey"):
            raise RuntimeError(f"Failed to delete object {key} from bucket {bucket_name}") from exc
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to delete object {key} from bucket {bucket_name}") from exc


def download_bytes_from_s3(*, bucket_name: str, key: str) -> bytes:
    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=bucket_name, Key=key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code == "404" or error_code == "NoSuchKey":
            raise RuntimeError(f"Object {key} does not exist in bucket {bucket_name}") from exc
        raise RuntimeError(f"Failed to download object {key} from bucket {bucket_name}: {error_code}") from exc
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to download object {key} from bucket {bucket_name}") from exc

    body = response.get("Body")
    if body is None:
        raise RuntimeError(f"No content returned for object {key} from bucket {bucket_name}")

    return body.read()


def get_character_image_s3_key(song_id: str, image_type: str = "reference") -> str:
    """
    Generate S3 key for character images.
    
    Args:
        song_id: Song UUID (as string)
        image_type: "reference" or "generated"
    
    Returns:
        S3 key path
    """
    if image_type == "reference":
        return f"songs/{song_id}/character_reference.jpg"
    elif image_type == "generated":
        return f"songs/{song_id}/character_generated.jpg"
    else:
        raise ValueError(f"Unknown image_type: {image_type}. Must be 'reference' or 'generated'")


