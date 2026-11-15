from temporalio.client import Client


class TemporalUnhealthyError(Exception):
    pass


class TemporalProbe:
    name = "temporal"

    def __init__(self, client: Client) -> None:
        self._client = client

    async def check(self) -> None:
        if not await self._client.service_client.check_health():
            raise TemporalUnhealthyError
