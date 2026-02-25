"""S3 client helpers for the LCA system."""
import io
import json
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError
import structlog

from backend.config import get_settings

logger = structlog.get_logger(__name__)

# In-memory storage for MOCK_AWS mode (no localstack required)
_in_memory_s3: Dict[str, Dict[str, bytes]] = {}


class InMemoryS3Client:
    """In-memory S3 client simulator for local development."""

    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str = None) -> None:
        if Bucket not in _in_memory_s3:
            _in_memory_s3[Bucket] = {}
        _in_memory_s3[Bucket][Key] = Body

    def get_object(self, Bucket: str, Key: str) -> Dict[str, Any]:
        if Bucket not in _in_memory_s3 or Key not in _in_memory_s3[Bucket]:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
                "GetObject"
            )
        body = _in_memory_s3[Bucket][Key]
        return {"Body": io.BytesIO(body), "ContentType": "application/octet-stream"}

    def head_object(self, Bucket: str, Key: str) -> Dict[str, Any]:
        if Bucket not in _in_memory_s3 or Key not in _in_memory_s3[Bucket]:
            raise ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "HeadObject"
            )
        return {"ContentLength": len(_in_memory_s3[Bucket][Key])}

    def generate_presigned_url(self, method: str, Params: Dict[str, str], ExpiresIn: int = 3600) -> str:
        bucket = Params.get("Bucket", "")
        key = Params.get("Key", "")
        return f"http://localhost:8000/mock-s3/{bucket}/{key}"


def _get_s3_client():
    """Get an S3 client, using in-memory storage if MOCK_AWS is enabled."""
    cfg = get_settings()
    if cfg.MOCK_AWS:
        logger.debug("using_in_memory_s3")
        return InMemoryS3Client()
    return boto3.client(
        "s3",
        region_name=cfg.AWS_REGION,
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
    )


def upload_file_bytes(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload raw bytes to S3. Returns the S3 key."""
    client = _get_s3_client()
    client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    return key


def upload_json(bucket: str, key: str, data: Dict[str, Any]) -> str:
    """Upload a JSON object to S3. Returns the S3 key."""
    body = json.dumps(data, indent=2, default=str).encode("utf-8")
    return upload_file_bytes(bucket, key, body, content_type="application/json")


def upload_text(bucket: str, key: str, text: str) -> str:
    """Upload text content to S3. Returns the S3 key."""
    return upload_file_bytes(bucket, key, text.encode("utf-8"), content_type="text/plain")


def download_bytes(bucket: str, key: str) -> bytes:
    """Download raw bytes from S3."""
    client = _get_s3_client()
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def download_json(bucket: str, key: str) -> Dict[str, Any]:
    """Download and parse a JSON file from S3."""
    data = download_bytes(bucket, key)
    return json.loads(data.decode("utf-8"))


def download_text(bucket: str, key: str) -> str:
    """Download text from S3."""
    return download_bytes(bucket, key).decode("utf-8")


def file_exists(bucket: str, key: str) -> bool:
    """Check whether a file exists in S3."""
    client = _get_s3_client()
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False


def get_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    """Generate a pre-signed download URL."""
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def stream_file(bucket: str, key: str):
    """Return a streaming body for a file in S3."""
    client = _get_s3_client()
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"], response.get("ContentType", "application/octet-stream")
