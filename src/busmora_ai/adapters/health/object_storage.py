import asyncio
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

from busmora_ai.config.settings import ObjectStorageSettings

if TYPE_CHECKING:
    # Dev-only stubs (types-boto3[s3]); not installed in runtime images.
    from types_boto3_s3.client import S3Client


class ObjectStorageProbe:
    """Checks the configured bucket is reachable with the configured credentials.

    Uses the generic S3 API with path-style addressing, so it works against any
    S3-compatible store (RustFS locally; the production vendor is chosen in T12).
    """

    name = "object_storage"

    def __init__(self, settings: ObjectStorageSettings, *, timeout_seconds: float = 2.0) -> None:
        self._settings = settings
        self._timeout = timeout_seconds

    async def check(self) -> None:
        await asyncio.to_thread(self._head_bucket)

    def _head_bucket(self) -> None:
        s = self._settings
        # boto3's overload set spans every AWS service; only the s3 overload is typed here.
        client: S3Client = boto3.client(  # pyright: ignore[reportUnknownMemberType]
            "s3",
            endpoint_url=s.endpoint_url,
            region_name=s.region,
            aws_access_key_id=s.access_key_id.get_secret_value(),
            aws_secret_access_key=s.secret_access_key.get_secret_value(),
            config=Config(
                s3={"addressing_style": "path"},
                connect_timeout=self._timeout,
                read_timeout=self._timeout,
                retries={"max_attempts": 1},
            ),
        )
        try:
            client.head_bucket(Bucket=s.bucket)
        finally:
            client.close()
