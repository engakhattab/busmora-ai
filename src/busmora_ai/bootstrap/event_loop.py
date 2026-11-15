import asyncio
import sys
from collections.abc import Coroutine
from typing import Any


def run(main: Coroutine[Any, Any, None]) -> None:
    """Run the role's main coroutine.

    psycopg's async driver cannot use Windows' default Proactor loop, so local
    development on Windows uses the selector loop. Linux containers are unaffected.
    """
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    asyncio.run(main, loop_factory=loop_factory)
