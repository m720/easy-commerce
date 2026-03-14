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


def generate_read_url(s3_key: str, expiry: int = None) -> Optional[str]:
    if not s3_key or not settings.S3_BUCKET_NAME:
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
    client = _get_client()
    client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
