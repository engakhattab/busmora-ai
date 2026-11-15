import os

import pytest
from pydantic import ValidationError

from busmora_ai.config.settings import AgentRoleSettings, CrawlRoleSettings, HttpRoleSettings

AGENT_ENV = {
    "BUSMORA_AI_POSTGRES__DSN": "postgresql://u:hunter2@localhost/db",
    "BUSMORA_AI_QDRANT__URL": "http://localhost:6333",
    "BUSMORA_AI_REDIS__URL": "redis://localhost:6379/0",
    "BUSMORA_AI_OBJECT_STORAGE__BUCKET": "b",
    "BUSMORA_AI_OBJECT_STORAGE__ACCESS_KEY_ID": "k",
    "BUSMORA_AI_OBJECT_STORAGE__SECRET_ACCESS_KEY": "s3cret",
}


@pytest.fixture(autouse=True)
def _isolate_from_local_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Never read the developer's .env or BUSMORA_AI_* variables in unit tests."""
    monkeypatch.chdir(tmp_path_factory.mktemp("cwd"))
    for key in list(os.environ):
        if key.startswith("BUSMORA_AI_"):
            monkeypatch.delenv(key)


def test_agent_settings_load_nested_values_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in AGENT_ENV.items():
        monkeypatch.setenv(key, value)

    settings = AgentRoleSettings()  # pyright: ignore[reportCallIssue]

    assert settings.qdrant.url == "http://localhost:6333"
    assert settings.health_server.port == 8101
    assert settings.temporal.address == "127.0.0.1:7233"


def test_secrets_never_appear_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in AGENT_ENV.items():
        monkeypatch.setenv(key, value)

    rendered = repr(AgentRoleSettings())  # pyright: ignore[reportCallIssue]

    assert "hunter2" not in rendered
    assert "s3cret" not in rendered


def test_missing_required_store_fails_fast() -> None:
    with pytest.raises(ValidationError):
        HttpRoleSettings()  # pyright: ignore[reportCallIssue]


def test_crawl_role_cannot_be_given_database_settings() -> None:
    assert "postgres" not in CrawlRoleSettings.model_fields
    assert "qdrant" not in CrawlRoleSettings.model_fields
