import asyncio
import sys
from collections.abc import Callable, Mapping

import pytest


def pytest_asyncio_loop_factories(
    config: pytest.Config,
    item: pytest.Item,
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]] | None:
    """Match bootstrap.event_loop: psycopg's async driver needs the selector loop on Windows."""
    if sys.platform == "win32":
        return {"selector": asyncio.SelectorEventLoop}
    return None
