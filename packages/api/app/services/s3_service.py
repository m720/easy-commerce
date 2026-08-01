import boto3
from botocore.exceptions import ClientError
from app.config import settings
from typing import Optional


def _get_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def generate_upload_url(s3_key: str, content_type: str) -> str:
    client = _get_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRY,
    )
    return url


def _is_direct_url(s3_key: str) -> bool:
    """True for images that are already reachable without S3.

    Seeded product photos are served by this API from /static, and images may
    also be pointed at an external host. Both are stored verbatim as the key.
    """
    return s3_key.startswith(("http://", "https://", "/"))


def generate_read_url(s3_key: str, expiry: int = None) -> Optional[str]:
    if not s3_key:
        return None
    if _is_direct_url(s3_key):
        return s3_key
    if not settings.S3_BUCKET_NAME:
        return None
    try:
        client = _get_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expiry or settings.S3_PRESIGNED_URL_EXPIRY,
        )
        return url
    except ClientError:
        return None


def delete_object(s3_key: str) -> None:
    # Directly-served images (seed data, external hosts) have no S3 object to remove.
    if not s3_key or _is_direct_url(s3_key) or not settings.S3_BUCKET_NAME:
        return
    client = _get_client()
    client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
