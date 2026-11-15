"""Export the published contracts into ``contracts/``, or check they are up to date.

    uv run python scripts/export_contracts.py           # regenerate
    uv run python scripts/export_contracts.py --check   # fail on drift (CI)

Outputs (committed; never edit by hand):
    contracts/temporal/manifest.json            task queues, activities, call options, errors
    contracts/temporal/<activity>.input.json    JSON Schema of the activity input
    contracts/temporal/<activity>.output.json   JSON Schema of the activity output
    contracts/ai-http/openapi.json              OpenAPI of the internal ai-http service
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from busmora_ai.entrypoints.http.app import create_http_app
from busmora_ai_contracts import ACTIVITIES, NonRetryableErrorType, TaskQueue
from busmora_ai_contracts import __version__ as contracts_version

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT / "contracts"


def _render(document: Any) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _schema(model: Any, title: str) -> dict[str, Any]:
    schema = TypeAdapter(model).json_schema(mode="serialization")
    schema.setdefault("title", title)
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema


def build_artifacts() -> dict[Path, str]:
    """Every generated file, keyed by its path relative to ``contracts/``."""
    files: dict[Path, str] = {}
    activities: list[dict[str, Any]] = []

    for spec in ACTIVITIES:
        stem = spec.name.value
        input_file = Path("temporal") / f"{stem}.input.json"
        output_file = Path("temporal") / f"{stem}.output.json"
        files[input_file] = _render(_schema(spec.input_type, f"{stem} input"))
        files[output_file] = _render(_schema(spec.output_type, f"{stem} output"))
        activities.append(
            {
                "name": stem,
                "task_queue": spec.task_queue.value,
                "status": spec.status,
                "input_schema": input_file.name,
                "output_schema": output_file.name,
                "recommended": {
                    "start_to_close_timeout_seconds": spec.start_to_close_seconds,
                    "heartbeat_timeout_seconds": spec.heartbeat_seconds,
                    "maximum_attempts": spec.max_attempts,
                },
            }
        )

    files[Path("temporal") / "manifest.json"] = _render(
        {
            "contracts_version": contracts_version,
            "task_queues": [queue.value for queue in TaskQueue],
            "non_retryable_error_types": [error.value for error in NonRetryableErrorType],
            "activities": activities,
        }
    )

    app = create_http_app(probes=(), timeout_seconds=1.0)
    files[Path("ai-http") / "openapi.json"] = _render(app.openapi())
    return files


def _existing_files() -> set[Path]:
    if not CONTRACTS_DIR.exists():
        return set()
    return {
        path.relative_to(CONTRACTS_DIR)
        for path in CONTRACTS_DIR.rglob("*")
        if path.is_file() and path.name != "README.md"
    }


def check(expected: dict[Path, str]) -> list[str]:
    problems: list[str] = []
    for relative, content in sorted(expected.items()):
        path = CONTRACTS_DIR / relative
        if not path.exists():
            problems.append(f"missing: contracts/{relative.as_posix()}")
        elif path.read_text(encoding="utf-8") != content:
            problems.append(f"out of date: contracts/{relative.as_posix()}")
    problems.extend(
        f"unexpected: contracts/{extra.as_posix()}"
        for extra in sorted(_existing_files() - expected.keys())
    )
    return problems


def write(expected: dict[Path, str]) -> None:
    for extra in _existing_files() - expected.keys():
        (CONTRACTS_DIR / extra).unlink()
    for relative, content in expected.items():
        path = CONTRACTS_DIR / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--check", action="store_true", help="fail if contracts/ is stale")
    args = parser.parse_args()

    expected = build_artifacts()
    if args.check:
        problems = check(expected)
        if problems:
            print("Contract drift detected. Run: uv run python scripts/export_contracts.py")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print(f"contracts/ is up to date ({len(expected)} files).")
        return 0

    write(expected)
    print(f"Wrote {len(expected)} files to contracts/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
