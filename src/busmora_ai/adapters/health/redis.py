from pydantic import SecretStr
from redis.asyncio import Redis


class RedisProbe:
    name = "redis"

    def __init__(self, url: SecretStr, *, timeout_seconds: float = 2.0) -> None:
        self._url = url
        self._timeout = timeout_seconds

    async def check(self) -> None:
        client: Redis = Redis.from_url(  # pyright: ignore[reportUnknownMemberType]  (untyped **kwargs)
            self._url.get_secret_value(),
            socket_connect_timeout=self._timeout,
            socket_timeout=self._timeout,
        )
        try:
            await client.ping()  # pyright: ignore[reportUnknownMemberType]
        finally:
            await client.aclose()
