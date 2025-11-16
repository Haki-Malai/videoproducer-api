from __future__ import annotations

import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from core.config import config

logger = logging.getLogger(__name__)

_session = boto3.session.Session()
_client = _session.client(
    "s3",
    endpoint_url=config.S3_ENDPOINT_URL,
    aws_access_key_id=config.S3_ACCESS_KEY_ID,
    aws_secret_access_key=config.S3_SECRET_ACCESS_KEY,
    region_name=config.S3_REGION,
)

_BUCKET_INITIALIZED = False


def ensure_bucket() -> None:
    """Ensure that the configured S3 bucket exists."""
    global _BUCKET_INITIALIZED
    if _BUCKET_INITIALIZED:
        return

    try:
        _client.head_bucket(Bucket=config.S3_BUCKET_NAME)
        _BUCKET_INITIALIZED = True
        return
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code not in ("404", "NoSuchBucket", "NotFound"):
            raise

    create_args = {"Bucket": config.S3_BUCKET_NAME}
    if config.S3_REGION != "us-east-1":
        create_args["CreateBucketConfiguration"] = {
            "LocationConstraint": config.S3_REGION
        }

    logger.info(
        "Creating bucket %s at %s",
        config.S3_BUCKET_NAME,
        config.S3_ENDPOINT_URL,
    )
    _client.create_bucket(**create_args)
    _BUCKET_INITIALIZED = True


def upload_file(path: str, key: str, content_type: Optional[str] = None) -> None:
    """Upload a local file to S3/MinIO.
    
    :param path: Local file path.
    :param key: Destination object key in the bucket.
    :param content_type: Optional content type to set for the object.
    """
    ensure_bucket()
    extra = {}
    if content_type:
        extra["ContentType"] = content_type

    _client.upload_file(
        Filename=path,
        Bucket=config.S3_BUCKET_NAME,
        Key=key,
        ExtraArgs=extra or None,
    )


def build_public_url(key: str) -> str:
    """Build a browser-facing URL for the given object key.
    
    :param key: Object key in the bucket.
    
    :return: Public URL to access the object.
    """
    base = config.S3_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/{key.lstrip('/')}"
