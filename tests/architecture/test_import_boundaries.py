"""Static import rules (ports and adapters, BTD-ADR-13; LLM isolation, docs/adr/0005).

- ``application`` and ``domain`` never import adapters, entrypoints or bootstrap.
- ``entrypoints`` call use cases; they never import adapters (wiring is in bootstrap/main_*).
- Each external SDK is imported only by the layer that owns it.
"""

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "busmora_ai"

SDK_OWNERS: dict[str, tuple[str, ...]] = {
    "litellm": ("adapters/llm/",),
    "scrapling": ("adapters/crawler/",),
    "playwright": ("adapters/crawler/",),
    "psycopg": ("adapters/",),
    "sqlalchemy": ("adapters/",),
    "qdrant_client": ("adapters/",),
    "redis": ("adapters/",),
    "boto3": ("adapters/",),
    "botocore": ("adapters/",),
    "fastapi": ("entrypoints/http/",),
    "uvicorn": ("bootstrap/", "main_"),
    "temporalio": ("adapters/", "entrypoints/activities/", "bootstrap/"),
}

FORBIDDEN_INTERNAL: dict[str, tuple[str, ...]] = {
    "application/": ("busmora_ai.adapters", "busmora_ai.entrypoints", "busmora_ai.bootstrap"),
    "domain/": (
        "busmora_ai.adapters",
        "busmora_ai.entrypoints",
        "busmora_ai.bootstrap",
        "busmora_ai.application",
    ),
    "entrypoints/": ("busmora_ai.adapters", "busmora_ai.bootstrap"),
    "adapters/": ("busmora_ai.entrypoints", "busmora_ai.bootstrap"),
}


def _modules() -> list[tuple[str, set[str]]]:
    result: list[tuple[str, set[str]]] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        result.append((path.relative_to(PACKAGE_ROOT).as_posix(), imported))
    return result


MODULES = _modules()


def test_package_was_found() -> None:
    assert MODULES, PACKAGE_ROOT


@pytest.mark.parametrize(("sdk", "owners"), SDK_OWNERS.items())
def test_sdk_is_imported_only_by_its_owner(sdk: str, owners: tuple[str, ...]) -> None:
    offenders = [
        module
        for module, imports in MODULES
        if any(name == sdk or name.startswith(f"{sdk}.") for name in imports)
        and not module.startswith(owners)
    ]
    assert offenders == [], f"{sdk} may only be imported under {owners}"


@pytest.mark.parametrize(("layer", "forbidden"), FORBIDDEN_INTERNAL.items())
def test_layer_dependency_direction(layer: str, forbidden: tuple[str, ...]) -> None:
    offenders = [
        (module, name)
        for module, imports in MODULES
        if module.startswith(layer)
        for name in imports
        if name.startswith(forbidden)
    ]
    assert offenders == []
