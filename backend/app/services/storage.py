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


