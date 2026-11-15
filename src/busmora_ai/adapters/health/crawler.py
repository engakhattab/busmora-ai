import importlib.util


class CrawlerNotInstalledError(Exception):
    """The ``crawl`` extra is missing: run ``uv sync --extra crawl`` (docs/adr/0006)."""


class CrawlerProbe:
    """Reports whether the browser-capable crawler dependencies are installed.

    Looks up top-level packages only, so neither Scrapling nor its browser stack is
    imported here. ``playwright`` arrives only through ``scrapling[fetchers]``.
    """

    name = "crawler"

    async def check(self) -> None:
        for package in ("scrapling", "playwright"):
            if importlib.util.find_spec(package) is None:
                raise CrawlerNotInstalledError(package)
