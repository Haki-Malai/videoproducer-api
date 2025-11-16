from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

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
    """Upload a local file to S3/MinIO."""
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
    """Build a browser-facing URL for the given object key."""
    base = config.S3_PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/{key.lstrip('/')}"


def build_s3_uri(key: str, bucket: str | None = None) -> str:
    bucket_name = bucket or config.S3_BUCKET_NAME
    normalized_key = key.lstrip("/")
    return f"s3://{bucket_name}/{normalized_key}"


def is_s3_uri(value: str | None) -> bool:
    return bool(value and value.startswith("s3://"))


def _resolve_bucket_and_key(value: str) -> tuple[str, str]:
    if is_s3_uri(value):
        parsed = urlparse(value)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if not bucket or not key:
            raise ValueError(f"Invalid S3 URI: {value}")
        return bucket, key
    return config.S3_BUCKET_NAME, value.lstrip("/")


def download_file(key_or_uri: str, destination: str) -> None:
    """Download the provided object to a local path."""
    bucket, key = _resolve_bucket_and_key(key_or_uri)
    if bucket == config.S3_BUCKET_NAME:
        ensure_bucket()
    _client.download_file(Bucket=bucket, Key=key, Filename=destination)


def generate_presigned_upload(
    key: str,
    *,
    content_type: str | None = None,
    expires_in: int = 3600,
    max_file_size: int | None = None,
) -> dict[str, object]:
    """Generate a presigned POST so browsers can upload directly to S3."""
    ensure_bucket()
    fields = {}
    conditions: list[object] = []
    if content_type:
        fields["Content-Type"] = content_type
        conditions.append({"Content-Type": content_type})
    if max_file_size:
        conditions.append(["content-length-range", 1, max_file_size])

    return _client.generate_presigned_post(
        Bucket=config.S3_BUCKET_NAME,
        Key=key,
        Fields=fields or None,
        Conditions=conditions or None,
        ExpiresIn=expires_in,
    )
