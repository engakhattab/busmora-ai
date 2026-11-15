from pydantic import SecretStr
from qdrant_client import AsyncQdrantClient


class QdrantProbe:
    name = "qdrant"

    def __init__(self, url: str, *, api_key: SecretStr | None, timeout_seconds: int = 2) -> None:
        self._url = url
        self._api_key = api_key
        self._timeout = timeout_seconds

    async def check(self) -> None:
        client = AsyncQdrantClient(
            url=self._url,
            api_key=self._api_key.get_secret_value() if self._api_key else None,
            timeout=self._timeout,
        )
        try:
            await client.get_collections()
        finally:
            await client.close()
