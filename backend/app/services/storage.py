from __future__ import annotations

from functools import lru_cache
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings


@lru_cache
def _get_s3_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )


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


def download_bytes_from_s3(*, bucket_name: str, key: str) -> bytes:
    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=bucket_name, Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Failed to download object {key} from bucket {bucket_name}") from exc

    body = response.get("Body")
    if body is None:
        raise RuntimeError(f"No content returned for object {key} from bucket {bucket_name}")

    return body.read()


