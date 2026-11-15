from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from busmora_ai.config.settings import TemporalSettings


async def connect_temporal(settings: TemporalSettings) -> Client:
    """Connect with the Pydantic data converter so contract models cross the wire as JSON."""
    api_key = settings.api_key.get_secret_value() if settings.api_key else None
    return await Client.connect(
        settings.address,
        namespace=settings.namespace,
        api_key=api_key,
        tls=api_key is not None,
        data_converter=pydantic_data_converter,
    )
