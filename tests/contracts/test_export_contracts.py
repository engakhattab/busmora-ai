import importlib.util
import json
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "export_contracts.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("export_contracts", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_is_deterministic() -> None:
    script = _load_script()
    assert script.build_artifacts() == script.build_artifacts()


def test_manifest_lists_every_activity_with_its_schemas() -> None:
    files = _load_script().build_artifacts()
    manifest = json.loads(files[Path("temporal") / "manifest.json"])

    names = {activity["name"] for activity in manifest["activities"]}
    assert names == {"ai.ping", "crawl.ping", "ai.run_agent_step", "crawl.crawl_sources"}
    for activity in manifest["activities"]:
        assert Path("temporal") / activity["input_schema"] in files
        assert Path("temporal") / activity["output_schema"] in files


def test_agent_step_output_schema_is_a_discriminated_union() -> None:
    files = _load_script().build_artifacts()
    schema = json.loads(files[Path("temporal") / "ai.run_agent_step.output.json"])

    assert schema["discriminator"]["propertyName"] == "outcome"
    assert set(schema["discriminator"]["mapping"]) == {
        "continue",
        "needs_crawl",
        "needs_clarification",
        "completed",
    }


def test_committed_contracts_are_up_to_date() -> None:
    script = _load_script()
    assert script.check(script.build_artifacts()) == []
